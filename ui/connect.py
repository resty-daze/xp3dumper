import zmq
          
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect ("tcp://localhost:10010")
          
for request in range (1,3):
    socket.send ("Hello")
    print socket.recv()