import time
import threading

class Server(threading.Thread):
  def run(self):
    import zmq
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:10010")
          
    while True:
        message = socket.recv()
        time.sleep (1)
        socket.send("World")
	
s = Server()
s.start()
s.join()
