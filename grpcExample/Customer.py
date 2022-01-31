import grpc
import week3_pb2
import week3_pb2_grpc
import time
import sys
import threading
import argparse
import random
class Customer:
    def __init__(self, id,ports):
        # unique ID of the Customer
        self.id = id
        self.ports = ports
        # a list of received messages used for debugging purpose
        self.recvMsg = list()
        # pointer for the stub
        self.stub = None
        self.clock = 0
        

    def createStub(self):

        channel = grpc.insecure_channel('localhost:{}'.format(random.choice(self.ports)))
        self.stub = week3_pb2_grpc.RPCServicerStub(channel)

    def request(self,  request, money):
        self.createStub()
        self.clock += 1
        if request == 'create':
            response = self.stub.MsgDelivery(week3_pb2.request_service(user=self.id, request='create', money=money, clock=self.clock))
            print("id "+str(self.id) +" create "+ str(response.success) +" money " + str(response.money))
        elif request == 'query':
            response = self.stub.MsgDelivery(week3_pb2.request_service(user=self.id, request='query', money=0, clock=self.clock))
            print("id "+str(self.id) +" query "+ str(response.success) +" money " + str(response.money))
        elif request == 'withdraw':
            response = self.stub.MsgDelivery(week3_pb2.request_service(user=self.id, request='withdraw', money=money, clock=self.clock))
            print("id "+str(self.id) +" withdraw "+ str(response.success) )
        elif request == 'deposit':
            response = self.stub.MsgDelivery(week3_pb2.request_service(user=self.id, request='deposit', money=money, clock=self.clock))
            print("id "+str(self.id) +" deposit "+ str(response.success) )
        elif request == 'q':
            exit()
        pass
def func(id):
    customer = Customer(id,None)
    if id == 2:
        customer.request('withdraw',400)
        pass
    if id == 3:
        customer.request('withdraw',400)
    customer.request('query',0)

def strip(s):
    return s.strip()
def get_port(number, file='grpcExample/resources/server_port_file.txt'):
    f = open(file, 'r')
    ports = f.readlines()
    ports = list(map(strip, ports))
    # home_port = ports[number]
    # ports.remove(home_port)
    return ports
def create_customer():
    names = ["Bill", "John", "Kyle", "Albert", "Josh"]
    numbers = "0123456789"
    return random.choice(names) + random.choice(numbers) + random.choice(numbers) + random.choice(numbers)
def check(customers, name):
    for customer in customers:
        if customer.id == name:
            return False
    return True
def random_requests():
    
    customers = []
    parser = argparse.ArgumentParser(description='Banking with GRPC.')
    parser.add_argument(dest='p', type=int, help='what port address in server port file are you.')
    args = parser.parse_args()
    port_number = args.p
    
    ports = get_port(port_number)
    # name = create_customer()
    name = 'John'
    if check(customers, name):
        customers.append(Customer(name, ports))
    
    customers[-1].request("create", 150 )# random.randint(100,201)
    # customers[-1].request("query", 0)
    # customers[-1].request("withdraw", 10)
    customers[-1].request("query", 0)
    customers[-1].request("deposit", 10)
    customers[-1].request("query", 0)
    # customers[-1].request("query", 0)
    # customers[-1].request("withdraw", 10)
    '''
    for choice in range(4):
        # choice = random.randint(0,4)
        choice = 3
        if choice == 0 :
            # create customer
            name = create_customer()
            if check(customers, name):
                customers.append(Customer(name, ports))
                customers[-1].request("create", random.randint(100,201))
            pass
        if choice == 1 :
            # query
            customer = random.choice(customers)
            customer.request("query", 0)
            pass
        if choice == 2 :
            # deposit
            customer = random.choice(customers)
            amount = random.randint(10, 126)
            customer.request("deposit", amount)
            pass
        if choice == 3 :
            # withdraw
            customer = random.choice(customers)
            # amount = random.randint(10, 126)
            amount = 150
            customer.request("withdraw", amount)
            pass
    '''
    
if __name__ == '__main__':
    random_requests()