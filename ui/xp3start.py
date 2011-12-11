import os
import errno
import subprocess
import shutil
import zmq
import time

import xp3proto_pb2
import getlist

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

class Workflow:
    def __init__(self, fileName, path, log, alert):
        self.fileName = fileName
        self.log = log
        self.alert = alert 
        self.path = path
    
    def start(self):
        self.context = zmq.Context(1)
        addr = self.getAddr()
        self.log("export_addr:%x" % addr)
        lists = getlist.getList()
        if len(lists) == 0:
           self.log("Finished: file list is empty.")
           return False
        self.log("load file lists[%s]" % str(map(lambda x : x[0], lists)))
        self.injectDll()
        # connect
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:10010")
        # set exporter addr
        req = xp3proto_pb2.Request()
        res = xp3proto_pb2.Response()
        req.type = xp3proto_pb2.Request.SET_EXPORT_ADDR
        req.expAddr = addr
        self.socket.send(req.SerializeToString())
        res.ParseFromString(self.socket.recv())
        self.log("set exporter addr [retval:%d]" % res.retVal)
        # for debug
        req.type  = xp3proto_pb2.Request.ALLOC_CONSOLE
        self.socket.send(req.SerializeToString())
        self.socket.recv()
        # check png dll
        self.checkPngDll()
        # dump file
        for it in lists:
            self.dumpFileList(it[0], it[1])
        self.alert("Dump Finished")
        self.haltTarget()

    def getAddr(self):
        self.log("try to get export addr")
        addrTool = createAddrTool(self.fileName)
        addrTool.setup()
        # start target
        proc = subprocess.Popen(self.fileName.encode('mbcs'))
        self.log("target process started[pid:%d]" % proc.pid)

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
            res.ParseFromString(self.socket.recv())
            self.log("load png dll [dll:%s][%s]" % (req.pngPluginPath, res.description))

def start(fileName, path, log, alert):
    log("start to process. [Target:%s][Path:%s]" % (fileName, path))
    Workflow(fileName, path, log, alert).start()
    


