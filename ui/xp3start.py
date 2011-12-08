import os
import shutil

def start(fileName, log):
    log("start to process. [Target:%s]" % fileName)
    shutil.copyfile("tools/!get_addr.tpm", os.path.split(fileName)[0])
    
