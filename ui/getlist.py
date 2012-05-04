import wx
import codecs
import string
import os
import subprocess
import locale

log = 0

class ACDetect:
    def __init__(self):
        self.path = os.getcwd() + "\\tools\\arc_conv.exe"
        self.detected = False
        if os.path.exists(self.path):
            self.detected = True

    def genFile(self, xp3Path, outPath):
        coding = 'mbcs'
        result_str = '"%s" %s %s "%s" "%s"' % (self.path, "--mod", "xp3list", outPath.encode(coding), xp3Path.encode(coding))
        log(result_str)
        try:
            tmp_bat = open("gen_file.bat", "w")
            print >> tmp_bat, result_str
            tmp_bat.close()
            retVal = subprocess.call(["gen_file.bat"])
            if retVal == 0:
                return True
        except:
            pass
        return False

def loadXp3Content(acd, fileName):
    # generate a temp file name
    outputFile = acd.outputPath + '/' + os.path.split(fileName)[1] + '.txt'
    
    if acd.genFile(fileName, outputFile):
        return (fileName, readTxtFile(outputFile))
    else:
        return (fileName, [])
                
def openTxtList():
    dlg = wx.FileDialog(None,
                        message = "Choose file lists to process",
                        wildcard= "*.txt",
                        style = wx.FD_OPEN | wx.FD_MULTIPLE)
    if dlg.ShowModal() != wx.ID_OK:
        return []
    return map(loadFileContent, dlg.GetPaths())

def openXp3List(acd):
    dlg = wx.FileDialog(None,
                        message = "Choose xp3 files to process",
                        wildcard = "*.xp3",
                        style = wx.FD_OPEN | wx.FD_MULTIPLE)
    if dlg.ShowModal() != wx.ID_OK:
        return []
    paths = dlg.GetPaths()
    result = []
    for p in paths:
        result.append(loadXp3Content(acd, p))
    return result

def readTxtFile(fileName):
    """ Output: a list with each line in the txt file. """
    f = open(fileName, 'r')
    sample = f.read(4)
    f.close()
    if sample.startswith(codecs.BOM_UTF16_LE) or sample.startswith(codecs.BOM_UTF16_BE):
        f = codecs.open(fileName, 'r', encoding='utf-16')
    elif sample.startswith(codecs.BOM_UTF8):
        f = codecs.open(fileName, 'r', encoding='utf-8')
    else:
        f = open(fileName, 'r')
    result = map(string.strip, f.readlines())
    f.close()
    return result

def loadFileContent(fileName):
    return (fileName, readTxtFile(fileName))

                
def getList(outputPath):
    acd = ACDetect()
    if acd.detected:
        acd.outputPath = outputPath
        return openXp3List(acd)
    else:
        return openTxtList()
