import os
import subprocess
import shutil
import zmq

import xp3proto_pb2
import getlist

class Workflow:
    def __init__(self, fileName, log):
        self.fileName = fileName
        self.log = log
    
    def start(self):
        self.context = zmq.Context()
        addr = self.getAddr()
        self.log("export_addr=%x" % addr)
        lists = getlist.getList()
        if len(lists) == 0:
            self.log("Finished: file list is empty.")
            return False
        self.log("load file lists[%s]" % str(map(lambda x : x[0], lists)))

    def getAddr(self):
        self.log("try to get export addr")
        shutil.copy("tools/!get_addr.tpm", os.path.split(self.fileName)[0])
        proc = subprocess.Popen(self.fileName.encode('mbcs'))
        self.log("target process started[pid=%d]" % proc.pid)
        socket = self.context.socket(zmq.REQ)
        socket.connect("tcp://localhost:10010")
        req = xp3proto_pb2.Request()
        req.type = xp3proto_pb2.Request.GET_EXPORT_ADDR
        socket.send(req.SerializeToString())
        res = xp3proto_pb2.Response()
        res.ParseFromString(socket.recv())
        addr = res.expAddr
        req.type = xp3proto_pb2.Request.EXIT
        socket.send(req.SerializeToString())
        proc.wait() 
        os.remove(os.path.split(self.fileName)[0] + "/!get_addr.tpm")
        return addr

def start(fileName, log):
    log("start to process. [Target:%s]" % fileName)
    Workflow(fileName, log).start()
    
