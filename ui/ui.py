import sys
import os
import traceback
import wx
import xp3start

class MainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="xp3dumper front-end", style=wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX)
        self.sizerBack = wx.BoxSizer(wx.VERTICAL)
		
        self.pathSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizerBack.Add(self.pathSizer, 0, wx.EXPAND, 0)
        
        self.pathSizer.Add(wx.StaticText(self, label = "Path: "))

        self.pathTxt = wx.TextCtrl(self)
        self.pathTxt.SetValue(os.getcwd() + "\\output")
        self.pathSizer.Add(self.pathTxt, wx.EXPAND)

        self.selectPathButton = wx.Button(self, label = "...", size=(20, -1))
        self.Bind(wx.EVT_BUTTON, self.selectPath, self.selectPathButton)
        self.pathSizer.Add(self.selectPathButton)

        self.addrChkBox = wx.CheckBox(self, label = "Get address by replace wuvorbis.dll")
        self.sizerBack.Add(self.addrChkBox)

        self.dummyPngChkBox = wx.CheckBox(self, label = "Cut dummy png.dll")
        self.sizerBack.Add(self.dummyPngChkBox)
        
#        self.skipDummyFileChkBox = wx.CheckBox(self, label= "Skip dummy file name")
#        self.sizerBack.Add(self.skipDummyFileChkBox)

        self.startButton = wx.Button(self, label = "Start")
        self.Bind(wx.EVT_BUTTON, self.OnStart, self.startButton)
        self.sizerBack.Add(self.startButton)
        
        #self.advanceButton = wx.Button(self, label = "I need advanced function")
        #self.Bind(wx.EVT_BUTTON, self.OnAdvanceStart, self.advanceButton)
        #self.sizerBack.Add(self.advanceButton)

        self.logList = wx.TextCtrl(self, size=(500,500), style = wx.TE_MULTILINE | wx.TE_READONLY)
        self.sizerBack.Add(self.logList)
        
        self.SetSizer(self.sizerBack)
        self.SetAutoLayout(1)
        self.sizerBack.Fit(self)
        self.sizerBack.Layout()
		
    def OnStart(self, e):
        self.disableButtons()
        fileDlg = wx.FileDialog(self, message = "choose target exe:", wildcard = "*.exe")
        ret = fileDlg.ShowModal()
        if ret==wx.ID_OK:
            fileName = fileDlg.GetPath()
            fileDlg.Destroy()
            try:
                if self.addrChkBox.GetValue():
                    xp3start.option["addr_method"] = "dll"
                else:
                    xp3start.option["addr_method"] = "tpm"
                xp3start.option["dummy_png"] = self.dummyPngChkBox.GetValue()
#                xp3start.option["dummy_file"] = self.skipDummyFileChkBox.GetValue()
                xp3start.start(fileName, self.pathTxt.GetValue(), self.addLog, self.alert)
            except Exception as e:
                self.addLog("process failed.")
                self.addLog(traceback.format_exc(5))

        self.enableButtons()
		
    def OnAdvanceStart(self, e):
        dlg = wx.MessageDialog(self, "now not usable.", "xp3dumper ui", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def disableButtons(self):
        self.startButton.Disable()
        #self.advanceButton.Disable()

    def enableButtons(self):
        self.startButton.Enable()
        #self.advanceButton.Enable()
    
    def addLog(self, msg):
        self.logList.AppendText(msg + '\n')

    def alert(self, msg):
        dlg = wx.MessageDialog(self, 
                               message=msg,
                               caption="xp3ui",
                               style=wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def selectPath(self, e):
        dlg = wx.DirDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            self.pathTxt.SetValue(dlg.GetPath())
        dlg.Destroy()
		
if __name__=="__main__":
    app = wx.App(False)
    MainFrame(None).Show()
    app.MainLoop()
	
