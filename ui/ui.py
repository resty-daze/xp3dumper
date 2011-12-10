import sys
import traceback
import wx
import xp3start

class MainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="xp3dumper front-end")
        self.sizerBack = wx.BoxSizer(wx.VERTICAL)

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
		
    def OnStart(self, e):
        self.disableButtons()
        fileDlg = wx.FileDialog(self, message = "choose target exe:", wildcard = "*.exe")
        ret = fileDlg.ShowModal()
        if ret==wx.ID_OK:
            fileName = fileDlg.GetPath()
            fileDlg.Destroy()
            try:
                xp3start.start(fileName, self.addLog, self.alert)
            except Exception,e:
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
		
if __name__=="__main__":
    app = wx.App(False)
    MainFrame(None).Show()
    app.MainLoop()
	
