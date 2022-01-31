cls
@REM update
@REM call python3 -m pip3 install --upgrade pip3
@REM setup
@REM call pip3 install virtualenv 
@REM call python3 -m venv grpcExample


@REM call "grpcExample/Scripts/python" -m "pip" install grpcio
@REM call "grpcExample/Scripts/python" -m "pip" install grpcio-tools
cd grpcExample
call "Scripts/python" -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. week3.proto
cd ..
@REM program
start grpcExample/Scripts/python grpcExample/Branch.py 0
start grpcExample/Scripts/python grpcExample/Branch.py 1
start grpcExample/Scripts/python grpcExample/Branch.py 2

timeout 5

start grpcExample/Scripts/python grpcExample/Customer.py 0
timeout 1
start grpcExample/Scripts/python grpcExample/Customer.py 1
timeout 1
start grpcExample/Scripts/python grpcExample/Customer.py 2
timeout 1

@REM deactivate
timeout 5
@REM taskkill /t /f /im conhost.exe      
taskkill /t /f /im python.exe
exit 0