import wx
import codecs
import string

def openTxtList():
    dlg = wx.FileDialog(None,
                        message = "Choose file lists to process",
                        wildcard= "*.txt",
                        style = wx.FD_OPEN | wx.FD_MULTIPLE)
    if dlg.ShowModal() != wx.ID_OK:
        return []
    return map(readTxtFile, dlg.GetPaths())

def readTxtFile(fileName):
    f = open(fileName, 'r')
    sample = f.read(4)
    f.close()
    if sample.startswith(codecs.BOM_UTF16_LE) or sample.startswith(codecs.BOM_UTF16_BE):
        f = codecs.open(fileName, 'r', encoding='utf-16')
    elif sample.startswith(codecs.BOM_UTF8):
        f = codecs.open(fileName, 'r', encoding='utf-8')
    else:
        f = open(fileName, 'r')
    result = (fileName, map(string.strip, f.readlines()))
    f.close()
    return result

def getList():
    return openTxtList()
