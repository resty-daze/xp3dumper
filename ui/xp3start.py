import os
import subprocess
import shutil
import zmq
import time

import xp3proto_pb2
import getlist

class Workflow:
    def __init__(self, fileName, log, alert):
        self.fileName = fileName
        self.log = log
        self.alert = alert 
    
    def start(self):
        self.context = zmq.Context(1)
        addr = self.getAddr()
        self.log("export_addr=%x" % addr)
        lists = getlist.getList()
        if len(lists) == 0:
           self.log("Finished: file list is empty.")
           return False
        self.log("load file lists[%s]" % str(map(lambda x : x[0], lists)))
        self.injectDll()

    def getAddr(self):
        self.log("try to get export addr")
        # copy !get_addr.tpm to target directory
        shutil.copy("tools/!get_addr.tpm", os.path.split(self.fileName)[0])
        # start target
        proc = subprocess.Popen(self.fileName.encode('mbcs'))
        self.log("target process started[pid=%d]" % proc.pid)

        socket = self.context.socket(zmq.REQ)
        socket.connect("tcp://localhost:10010")

        req = xp3proto_pb2.Request()
        # request export addr
        req.type = xp3proto_pb2.Request.GET_EXPORT_ADDR
        socket.send(req.SerializeToString())
        res = xp3proto_pb2.Response()
        res.ParseFromString(socket.recv())
        addr = res.expAddr
        self.log("addr get")
        # request exit
        req.type = xp3proto_pb2.Request.EXIT
        socket.send(req.SerializeToString())
        proc.wait() 
        socket.close()

        # remove tpm file
        os.remove(os.path.split(self.fileName)[0] + "/!get_addr.tpm")
        return addr

    def injectDll(self): 
        self.log("try to get inject dumper.dll")
        # start target
        self.proc = subprocess.Popen(self.fileName.encode('mbcs'))
        self.log("target process started[pid=%d]" % self.proc.pid)
        # wait
        time.sleep(2)
        self.alert("Wait target process become stable, then click ok")
        # inject
        dll = os.getcwd() + "/tools/dumper.dll"
        pid = str(self.proc.pid)
        self.log("try inject dll[dll:%s][pid:%s]" % (dll, pid))
        subprocess.check_output(["tools/dllinject.exe", "remote", dll, pid], stderr=subprocess.STDOUT)
        self.log("inject over")
        # exit
        socket = self.context.socket(zmq.REQ)
        socket.connect("tcp://localhost:10010")

        # request exit
        req = xp3proto_pb2.Request()
        req.type = xp3proto_pb2.Request.EXIT
        socket.send(req.SerializeToString())
        self.proc.wait() 
        socket.close()

def start(fileName, log, alert):
    log("start to process. [Target:%s]" % fileName)
    Workflow(fileName, log, alert).start()
    


