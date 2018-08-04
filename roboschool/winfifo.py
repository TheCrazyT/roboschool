import time
import os
import win32pipe
import win32file
import win32event
import winerror
import pywintypes
import winnt
import io
import traceback
PIPE_PREFIX  = r"\\.\pipe\roboschool%s"
PIPE_HANDLES = {}
FIFO_DEBUG = False
def dbg(txt):
    global FIFO_DEBUG
    if FIFO_DEBUG:
        print("%05d# %s" % (os.getpid(),txt))
class FileIO(io.IOBase):
    def __init__(self,handle,fileName,overlapped,opt,waitForConnect):
        #win32pipe.SetNamedPipeHandleState(handle, win32pipe.PIPE_READMODE_BYTE, None, None)
        self.handle         = handle
        self.fileName       = fileName
        self.overlapped     = overlapped
        self.waitForConnect = waitForConnect
        if opt == win32file.GENERIC_WRITE:
            optStr = "GENERIC_WRITE"
        else:
            optStr = "GENERIC_READ"
        dbg("FileIO %s %s %s" % (handle,fileName,optStr))
    def write(self, x):
        dbg("write %d %s %s\n" % (self.handle,self.fileName,x))
        if self.waitForConnect:
            ret_code = win32event.WaitForSingleObject(self.overlapped.hEvent,10000)
            if ret_code != win32event.WAIT_OBJECT_0:
                dbg("write %d %s %s failed\n" % (self.handle,self.fileName,size))
                raise Exception("ret_code: %d" % ret_code);
            self.waitForConnect = False
        win32file.WriteFile(self.handle,x.encode("ascii"),self.overlapped)
        ret_code = win32event.WaitForSingleObject(self.overlapped.hEvent,10000)
        if ret_code != win32event.WAIT_OBJECT_0:
            raise Exception("ret_code: %d" % ret_code);
        dbg("write %d returned" % self.handle)
        return len(x)
    def read(self,size):
        #dbg("read %d %s %s\n" % (self.handle,self.fileName,size))
        #traceback.print_stack()
        result = winerror.ERROR_IO_PENDING
        if self.waitForConnect:
            ret_code = win32event.WaitForSingleObject(self.overlapped.hEvent,10000)
            if ret_code != win32event.WAIT_OBJECT_0:
                dbg("read %d %s %s failed\n" % (self.handle,self.fileName,size))
                raise Exception("ret_code: %d" % ret_code);
            self.waitForConnect = False
        result,data = win32file.ReadFile(self.handle,size,self.overlapped)
        ret_code = win32event.WaitForSingleObject(self.overlapped.hEvent,10000)
        if ret_code != win32event.WAIT_OBJECT_0:
            raise Exception("ret_code: %d" % ret_code);
        #dbg("read returned: size:%d  %s %s %s\n" % (size,result,bytes(data),ret_code))
        return bytes(data)
    def readline(self):
        dbg("readline %d %s\n" % (self.handle,self.fileName))
        res = str(super().readline(),"UTF-8")
        dbg("readline %d returned %s\n" % (self.handle,res))
        return res
    def flush(self):
        win32file.FlushFileBuffers(self.handle)
def open(name,options):
    if options == os.O_WRONLY:
        opt = win32file.GENERIC_WRITE
        dbg("open %s GENERIC_WRITE" % (name))
    else:
        opt = win32file.GENERIC_READ
        dbg("open %s GENERIC_READ" % (name))
    fileName = PIPE_PREFIX % name
    fileName = fileName.replace("\\","/")
    try:
        overlapped = pywintypes.OVERLAPPED()
        #TODO: this check is more a workaround than a real solution!
        if name in PIPE_HANDLES:
            pipe_handle = PIPE_HANDLES[name]
            overlapped.hEvent = win32event.CreateEvent(None, 0, 0, None)
            rc = win32pipe.ConnectNamedPipe(pipe_handle, overlapped)
            if rc == winerror.ERROR_PIPE_CONNECTED:
                win32event.SetEvent(overlapped.hEvent)
            return FileIO(pipe_handle,fileName,overlapped,opt,True )
        else:
            wh = win32file.CreateFile(
                fileName,
                opt,
                0,
                None,
                win32file.OPEN_EXISTING,
                win32file.FILE_FLAG_OVERLAPPED,
                None
            )
            #dbg("SetNamedPipeHandleState %s" % wh)
            #win32pipe.SetNamedPipeHandleState(wh,
            #                  win32pipe.PIPE_READMODE_BYTE, None, None)
            overlapped.hEvent = win32event.CreateEvent(None, 0, 0, None)
        return FileIO(wh,fileName,overlapped,opt,False )
    except:
        raise
        #return os.open(name,options)
def mkfifo(name):
        openMode = win32pipe.PIPE_ACCESS_DUPLEX | win32file.FILE_FLAG_OVERLAPPED
        #openMode = win32pipe.PIPE_ACCESS_INBOUND | win32file.FILE_FLAG_OVERLAPPED
        pipeMode = win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE
        #        | win32pipe.PIPE_NOWAIT
        fileName = PIPE_PREFIX % name
        fileName = fileName.replace("\\","/")
        sa = pywintypes.SECURITY_ATTRIBUTES()
        sa.SetSecurityDescriptorDacl ( 1, None, 0 )
        #for i in range(0,1):
        pipe_handle = win32pipe.CreateNamedPipe(fileName,
                                                openMode,
                                                pipeMode,
                                                10,65536,65536,300,None
                                                #win32pipe.PIPE_UNLIMITED_INSTANCES,
                                                #200,
                                                #0,
                                                #0,
                                                #2000,
                                                #sa
                                                )
        PIPE_HANDLES[name] = pipe_handle