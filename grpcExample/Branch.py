from concurrent import futures
import grpc
import week3_pb2
import week3_pb2_grpc
import sys
import random
import argparse
import logging
import os

from threading import Thread, Lock
# python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. week3.proto       #compile grpc
'''
launching instructions 
open code or terminal in folder. Make six windows to run everything

python Branch.py 1 # launches branch 1
python Branch.py 2 # launches branch 2
python Branch.py 3 # launches branch 3

python Customer.py 1 #launches customer 1, executes query, and exits
python Customer.py 2 #launches customer 2, executes deposit 170 then query, and exits
python Customer.py 3 #launches customer 3, executes withdraw 70 then query, and exits

'''

class Customer():
    def __init__(self, name,balance):
        self.name = name 
        self.balance = balance
        self.lock = Lock() 
    def deposit(self, amount):
        # self.lock.acquire()
        self.balance += amount
        # self.lock.release()
    def withdraw(self, amount):
        # self.lock.acquire()
        if amount > self.balance:
            # self.lock.release()
            return False
        self.balance -= amount
        # self.lock.release()
        return True
class Branch(week3_pb2_grpc.RPCServicer):

    def __init__(self, server_port, other_server_ports):
        # unique ID of the Branch
        self.id = server_port
        self.other_server_ports = other_server_ports
        # the list of Client stubs to communicate with the branches
        self.stubList = list()
        # a list of received messages used for debugging purpose
        self.recvMsg = list()
        self.customers = list()
        # iterate the processID of the branches
        # TODO: students are expected to store the processID of the branches
        self.connected = False
        self.clock = 0
        self.lock = Lock() #clock lock
        file = 'grpcExample/resources/transaction.{}.log'.format(self.id)
        if not os.path.exists(file):
            f = open(file, 'w')
            f.close()
        else:
            f = open(file, 'w')
            f.truncate(0)
            f.close()
        logging.basicConfig(filename=file, encoding='utf-8', level=logging.DEBUG)
        logging.info('SERVER CREATED::PORT:{}'.format(self.id))

    def setup(self):
        if self.connected:
            return
        for port in self.other_server_ports:
            channel = grpc.insecure_channel('localhost:{}'.format(port))
            s = week3_pb2_grpc.RPCServicerStub(channel)
            self.stubList.append(s)
        self.connected = True
        logging.info('SERVER CONNECTED::PORT{}'.format(self.id))

    def event_receive(self, request, rc):
        self.lock.acquire()
        self.clock = max(rc, self.clock) + 1
        # print(request+' event receive: clock ' +str( self.clock))
        self.lock.release()
    def event_execute(self, request):
        self.lock.acquire()
        self.clock += 1
        # print(request+' event execute: clock ' +str(self.clock))
        self.lock.release()
    def propagation_send(self, request):
        self.lock.acquire()
        self.clock += 1
        # print(request+' broadcast send clock ' +str( self.clock))
        self.lock.release()
    def propagation_receive(self, request,rc):
        self.lock.acquire()
        self.clock = max(rc, self.clock) + 1
        # print(request+' broadcst receive: clock ' +str( self.clock))
        self.lock.release()
    def propagation_execute(self, request):
        self.lock.acquire()
        self.clock += 1
        # print(request+' broadcst execute: clock ' +str( self.clock))
        self.lock.release()
    def propagation_response(self,request, rc):
        self.lock.acquire()
        self.clock = max(rc, self.clock) + 1
        # print(request+' broadcst response: clock ' +str( self.clock))
        self.lock.release()
    def event_response(self, request):
        self.lock.acquire()
        self.clock += 1
        # print(request+' event response: clock ' +str( self.clock))
        self.lock.release()
    def search(self,name):
        for customer in self.customers:
            if name == customer.name:
                return customer
        return None



    def error_action(self, request):
        logging.error('SERVER:{}::{}:[{}]::Amount:[{}]'.format(self.id, request.request, request.user, 0 ))
        return week3_pb2.success(success=False, money=0 , clock=self.clock)

    def create_action(self,request):
        success = True
        self.event_receive(request.request, request.clock)
        # if not customer:
        
        self.propagation_send(request.request)
        for stub in self.stubList:
            resp = stub.MsgDelivery(week3_pb2.request_service(user= request.user, request='prop_create', money=request.money,clock= self.clock))
            self.propagation_response(request.request, resp.clock)
            if not resp.success:
                success = False
        if success:
            self.event_execute(request.request)
            customer = Customer(request.user, request.money)
            self.customers.append(customer)
            logging.info('SERVER:{}::{}:[{}]::Amount:[{}]'.format(self.id,request.request, request.user, customer.balance ))
            self.event_response(request.request)
            return week3_pb2.success(success=True, money=customer.balance , clock=self.clock)
        else:
            logging.error('SERVER:{}::{}:[{}]::Amount:[{}]'.format(self.id,request.request, request.user, request.money ))
            self.event_response(request.request)
            return week3_pb2.success(success=False, money=request.money , clock=self.clock)
    def prop_create_action(self,request):
        self.event_receive(request.request, request.clock)
        # if not customer:
        self.event_execute(request.request)
        customer = Customer(request.user, request.money)
        self.customers.append(customer)
        logging.info('SERVER:{}::{}:[{}]::Amount:[{}]'.format(self.id,request.request, request.user, customer.balance ))
        self.event_response(request.request)
        return week3_pb2.success(success=True, money=customer.balance , clock=self.clock)
    def query(self,request,customer):
        logging.info('SERVER:{}::{}:[{}]::Amount:[{}]'.format(self.id,request.request, request.user, customer.balance ))
        return week3_pb2.success(success=True, money=customer.balance , clock=self.clock)    
    def withdraw_action(self, request, customer):
        success = True
        # logging.debug('1')
        for stub in self.stubList:
            resp = stub.MsgDelivery(week3_pb2.request_service(request='lock', user=request.user, money=request.money,clock= self.clock))
            # logging.debug('2')
            if not resp.success:
                success = resp.success
                # print("lock failed")

        # Local withdraw
        self.event_receive(request.request, request.clock)
        self.event_execute(request.request)
        if success:
            # logging.debug('3')
            customer.lock.acquire()
            customer.withdraw(request.money)
            customer.lock.release()
            # logging.debug('4')
            #prop withdraw
            self.propagation_send(request.request)
            for stub in self.stubList:
                resp = stub.MsgDelivery(week3_pb2.request_service(request='propagate_withdraw',user=request.user, money=request.money,clock= self.clock))
                self.propagation_response(request.request, resp.clock)
                
                if not resp.success:
                    logging.error('SERVER:{}::{}:[{}]::Amount:[{}]'.format(self.id, request.request, request.user, customer.balance ))
                    return week3_pb2.success(success=False, money=0,clock= self.clock)
        # logging.debug('5')
        for stub in self.stubList:
            resp = stub.MsgDelivery(week3_pb2.request_service(request='unlock', user=request.user, money=request.money,clock= self.clock))

        self.event_response(request.request)
        if success:
            logging.info('SERVER:{}::{}:[{}]::Amount:[{}]'.format(self.id,request.request, request.user, customer.balance ))
            return week3_pb2.success(success=True, money=0,clock= self.clock)
        else:
            return week3_pb2.success(success=False, money=0,clock= self.clock)
    def deposit_action(self,request,customer):
        self.event_receive(request.request, request.clock)
        success = True

        for stub in self.stubList:
            resp = stub.MsgDelivery(week3_pb2.request_service(request='lock', user=request.user, money=request.money,clock= self.clock))
            if not resp.success:
                success = resp.success
        
        self.event_execute(request.request)
        if success:
            customer.lock.acquire() 
            customer.deposit(request.money)
            customer.lock.release()
            
            #prop withdraw
            self.propagation_send(request.request)
            for stub in self.stubList:
                resp = stub.MsgDelivery(week3_pb2.request_service(request='propagate_deposit',user=request.user, money=request.money,clock= self.clock))
                self.propagation_response(request.request, resp.clock)
                
                if not resp.success:
                    logging.error('SERVER:{}::{}:[{}]::Amount:[{}]'.format(self.id,request.request, request.user, customer.balance ))
                    return week3_pb2.success(success=False, money=0,clock= self.clock)
        
        for stub in self.stubList:
            resp = stub.MsgDelivery(week3_pb2.request_service(request='unlock', user=request.user, money=request.money,clock= self.clock))

        self.event_response(request.request)
        logging.info('SERVER:{}::{}:[{}]::Amount:[{}]'.format(self.id,request.request, request.user, customer.balance ))
        return week3_pb2.success(success=True, money=0,clock= self.clock)
    def propagate_withdraw(self,request,customer):
        # update balance from other branch
            
        if customer.balance >= request.money:
            self.propagation_receive(request.request, request.clock)
            self.propagation_execute(request.request)
            # customer.lock.acquire()
            if customer.lock.locked():
                customer.withdraw(request.money)
                # customer.lock.release()
                logging.info('SERVER:{}::{}:[{}]::Amount:[{}]'.format(self.id,request.request, request.user, customer.balance ))
                return week3_pb2.success(success=True, money=0,clock= self.clock)
        else:
            
            return week3_pb2.success(success=False, money=0,clock= self.clock)
        

    def propagate_deposit(self,request,customer):
         
        self.propagation_receive(request.request, request.clock)
        self.propagation_execute(request.request)
        
        customer.deposit(request.money)
        logging.info('SERVER:{}::{}:[{}]::Amount:[{}]'.format(self.id,request.request, request.user, customer.balance ))
        return week3_pb2.success(success=True, money=0,clock= self.clock)

    def MsgDelivery(self,request, context):
        # logging.debug('0')
        self.setup()
        # self.recvMsg.append(request)
        customer = self.search(request.user)
        if 'create' not in request.request and not customer:
            return self.error_action(request)

        if request.request == 'create' and not customer:
            return self.create_action(request)
        elif request.request == 'prop_create' and not customer:
            return self.prop_create_action(request)
        elif request.request == 'query':
            return self.query(request,customer)
            
        elif request.request == 'withdraw' and customer.balance >= request.money:
            return self.withdraw_action(request,customer)
        elif request.request == 'deposit' and request.money > 0:
            return self.deposit_action(request, customer)

        elif request.request == 'propagate_withdraw' and customer.balance >= request.money:
            return self.propagate_withdraw(request,customer)
            # pass
        elif request.request == 'propagate_deposit' and request.money > 0:
            return self.propagate_deposit(request, customer)
            # pass
        elif  request.request == 'lock' :
            print(request.request, not customer.lock.locked())
            if not customer.lock.locked():
                customer.lock.acquire()
                return week3_pb2.success(success=True, money=0,clock= self.clock)
        elif request.request == 'unlock' :
            print(request.request, customer.lock.locked())
            if customer.lock.locked():
                customer.lock.release()
                return week3_pb2.success(success=True, money=0,clock= self.clock)

        return self.error_action(request)



# server setup helpers
def strip(s):
    return s.strip()
def get_port(number, file='grpcExample/resources/server_port_file.txt'):
    f = open(file, 'r')
    ports = f.readlines()
    ports = list(map(strip, ports))
    home_port = ports[number]
    ports.remove(home_port)
    return home_port, ports
# server
def serve():
    

    parser = argparse.ArgumentParser(description='Banking with GRPC.')
    parser.add_argument(dest='p', type=int, help='what port address in server port file are you.')
    args = parser.parse_args()
    port_number = args.p
    
    server_port,ports = get_port(port_number)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    week3_pb2_grpc.add_RPCServicerServicer_to_server(Branch(server_port, ports), server)

    server.add_insecure_port('[::]:{}'.format(server_port))
    # print('server {}'.format(str(server_port)))
    server.start()
    server.wait_for_termination()
    

if __name__ == '__main__':
    serve()