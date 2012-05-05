import os
import errno
import subprocess
import shutil
import zmq
import time

import xp3proto_pb2
import getlist

ZMQ_TIMEOUT = 5 * 1000 # 5s timeout for zmq socket

option = {}

class TpmAddr:
    def __init__(self, path):
        self.path = os.path.split(path)[0]

    def setup(self):
        # copy !get_addr.tpm to target directory
        shutil.copy("tools/!get_addr.tpm", self.path)

    def rollback(self):
        # remove tpm file
        os.remove(self.path + "/!get_addr.tpm")

class DllAddr:
    def __init__(self, path):
        self.path = os.path.split(path)[0]
    
    def setup(self):
        shutil.move(self.path + "/plugin/wuvorbis.dll", self.path + "/plugin/wuvorbis.dll.bak")
        shutil.copy("tools/!get_addr.tpm", self.path + "/plugin/wuvorbis.dll")

    def rollback(self):
        if os.path.exists(self.path + "/plugin/wuvorbis.dll.bak"):
            shutil.copy(self.path + "/plugin/wuvorbis.dll.bak", self.path + "/plugin/wuvorbis.dll")
            os.remove(self.path + "/plugin/wuvorbis.dll.bak")

addrTools = {'tpm' : TpmAddr,
             "dll" : DllAddr}
def createAddrTool(path):
    return addrTools[option["addr_method"]](path)

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else: raise

context = zmq.Context(1)

class Workflow:
    def __init__(self, fileName, path, log, alert):
        self.fileName = fileName
        self.log = log
        self.alert = alert 
        self.path = path
    
    def prepare(self):
        self.context = context
        return self

    def recv(self):
        poller = zmq.Poller()
        poller.register(self.socket, zmq.POLLIN)
        if poller.poll(ZMQ_TIMEOUT):
            return self.socket.recv()
        else:
            raise IOError("Timeout when recv zmq message.")

    def close_socket(self):
        self.socket.close()

    def start(self):
        self.prepare()
        addr = self.getAddr()
        self.log("export_addr:%x" % addr)
        lists = getlist.getList(self.path)
        if len(lists) == 0:
           self.log("Finished: file list is empty.")
           return False
        self.log("load file lists[%s]" % str(map(lambda x : x[0], lists)))
        self.injectDll()
        # connect
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:10010")
        self.socket.setsockopt(zmq.LINGER, 0)
        # set exporter addr
        req = xp3proto_pb2.Request()
        res = xp3proto_pb2.Response()
        req.type = xp3proto_pb2.Request.SET_EXPORT_ADDR
        req.expAddr = addr
        self.socket.send(req.SerializeToString())
        res.ParseFromString(self.recv())
        self.log("set exporter addr [retval:%d]" % res.retVal)
        # for debug
        req.type  = xp3proto_pb2.Request.ALLOC_CONSOLE
        self.socket.send(req.SerializeToString())
        self.recv()
        # for dummy png
        if ("dummy_png" in option) and option["dummy_png"]:
            req.type = xp3proto_pb2.Request.PNG_DUMMY_CUT
            self.socket.send(req.SerializeToString())
            self.recv()
        # check png dll
        self.checkPngDll()
        # dump file
        for it in lists:
            self.dumpFileList(it[0], it[1])
        self.alert("Dump Finished")
        self.haltTarget()
        return self

    def getAddr(self):
        self.log("try to get export addr")
        addrTool = createAddrTool(self.fileName)
        addrTool.setup()
        # start target
        self.proc = subprocess.Popen(self.fileName.encode('mbcs'))
        self.log("target process started[pid:%d]" % self.proc.pid)

        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:10010")

        req = xp3proto_pb2.Request()
        # request export addr
        req.type = xp3proto_pb2.Request.GET_EXPORT_ADDR
        self.socket.send(req.SerializeToString())
        res = xp3proto_pb2.Response()
        res.ParseFromString(self.recv())
        addr = res.expAddr
        self.log("addr get")
        # request exit
        req.type = xp3proto_pb2.Request.EXIT
        self.socket.send(req.SerializeToString())
        self.proc.wait() 
        self.socket.close()
        addrTool.rollback()
        return addr

    def injectDll(self): 
        self.log("try to get inject dumper.dll")
        # start target
        self.proc = subprocess.Popen(self.fileName.encode('mbcs'))
        self.log("target process started[pid:%d]" % self.proc.pid)
        # wait
        time.sleep(2)
        self.alert("Wait target process become stable, then click ok")
        # inject
        dll = os.getcwd() + "\\tools\\dumper.dll"
        pid = str(self.proc.pid)
        self.log("try inject dll[dll:%s][pid:%s]" % (dll, pid))
        subprocess.check_output(["tools\\dllinject.exe", "remote", dll, pid], stderr=subprocess.STDOUT)
        self.log("inject over")

    def dumpFileList(self, fileName, fileList):
        fileName = os.path.split(fileName)[1]
        dumpPath = self.path + "\\" + fileName
        for f in fileList:
            mkdir_p(os.path.split(dumpPath + "\\" + f)[0])
        req = xp3proto_pb2.Request()
        req.type = xp3proto_pb2.Request.EXTRACT_FILE
        req.fileToExtract.extend(fileList)
        req.extractPath = dumpPath
        self.socket.send(req.SerializeToString())
        res = xp3proto_pb2.Response()
        res.ParseFromString(self.socket.recv())
        if res.retVal == 0:
            self.log("dump file list [%s] success" % fileName)
        else:
            self.log("dump file list [%s] failed: [%s]" % (fileName, res.description))  

    def haltTarget(self):
        # request exit
        if self.proc.poll() == None:
            self.proc.terminate()
            
    def checkPngDll(self):
        if os.path.exists(os.getcwd() + "\\tools\\layerExSave.dll"):
            self.log("detected tools\\layerExSave.dll")
            req = xp3proto_pb2.Request()
            req.type = xp3proto_pb2.Request.INIT_PNG_PLUGIN
            req.pngPluginPath = os.getcwd() + "\\tools\\layerExSave.dll"
            self.socket.send(req.SerializeToString())
            res = xp3proto_pb2.Response()
            res.ParseFromString(self.recv())
            self.log("load png dll [dll:%s][%s]" % (req.pngPluginPath, res.description))

def start(fileName, path, log, alert):
    getlist.log=log
    log("start to process. [Target:%s][Path:%s]" % (fileName, path))
    
    try:
        wf = Workflow(fileName, path, log, alert)
        wf.start()
    finally:
        wf.haltTarget()
    
def get_addr(fileName, path, log, alert):
    getlist.log=log
    return Workflow(fileName, path, log, alert).prepare().getAddr()
