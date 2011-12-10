#include <cstdio>
#include <sstream>
#include <windows.h>
#include "zmq_wrapper.h"
#include "stub/tp_stub.h"

using namespace std;

const int kPathLen = 1024;

int onStart_dumper(void*);
/// Entry Point
extern "C"
BOOL WINAPI 
DllMain(HANDLE hinstDLL, DWORD dwReason, LPVOID lpvReserved) {
    switch (dwReason) {
    case DLL_PROCESS_ATTACH:
        CreateThread( NULL, 0, (LPTHREAD_START_ROUTINE) onStart_dumper, NULL, 0, 0);
        break;
    case DLL_PROCESS_DETACH:
        break;
    }
    return TRUE;
}

//////////////////////////////////////////////////////////////////

/// allocate a console : to display log
static void make_console() {
    AllocConsole();
    freopen("CONOUT$", "w", stdout);
    freopen("CONIN$", "r", stdin);
}

/// raii helper class for extract_file 
struct ExFileRAII {
    IStream * st;
    HANDLE hFile;
    ExFileRAII() {
        st = NULL;
        hFile = INVALID_HANDLE_VALUE;
    }
    ~ExFileRAII() {
        if (st != NULL) {
            st->Release();
        }
        if (hFile != INVALID_HANDLE_VALUE)  {
            CloseHandle(hFile);
        }
    }
};
/// extract a file
static int extract_file(const char * path, // path to save, (utf-8)
                        const char * name, // file to save, (utf-8)
                        string & desc) {   // error description
    wchar_t wpath[kPathLen];
    wchar_t wname[kPathLen];
    MultiByteToWideChar(CP_UTF8, 0, path, strlen(path) + 1, wpath, sizeof(wpath));
    MultiByteToWideChar(CP_UTF8, 0, path, strlen(name) + 1, wname, sizeof(wname));
    
    ExFileRAII holder;
    IStream * st = TVPCreateIStream(ttstr(wname), TJS_BS_READ);
    if (st == NULL) {
        desc = "Error: failed open file: ";
        desc += name;
        return 2;
    }
    holder.st = st;

    STATSTG t;
    st->Stat(&t, STATFLAG_DEFAULT);
    unsigned long long ss = t.cbSize.QuadPart, now = 0;
    
    wstring str = wpath;
    str += L"/";
    str += wname;
    HANDLE hFile = CreateFileW(str.c_str(), GENERIC_WRITE, FILE_SHARE_WRITE, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (hFile == INVALID_HANDLE_VALUE) {
        stringstream sstr;
        sstr << "Error: failed open file to write[file=" << name << "]" << "[errcode=" << GetLastError() << "]"; 
        desc = sstr.str();
        return 2;
    }
    holder.hFile = hFile;
    ULONG size, os, tmp;
    static char buffer[1024 * 64];
    
    while (now < ss) {	
        if ((st->Read(&buffer, sizeof(buffer), &size)) != S_OK) {
            wprintf(L"failed read data : %s\n", wname);
            desc = "Error: failed read data from stream. [fname=";
            desc = desc + name + "]";
            return 2;
        }
        now += size;
        tmp = 0;
        while (tmp < size) {
            WriteFile(hFile, buffer, size, &os, NULL);
            tmp += os;
        }
    }
	
    wprintf(L"%s\n", wname);
    return 0;
}

/// on start
/// start a zmq server to handle request
int onStart_dumper(void*) {
    Sleep(2);
    void *responder = rep_sock ("tcp://*:10010");
    while (true) {
        xp3::Request req;
        if (recv_req(responder, req)) {
            printf("recv a new request\n");
            xp3::Response res;
            res.set_retval(0);
            switch(req.type()) {
            case xp3::Request::EXIT:
                exit(0);
                break;
            case xp3::Request::SET_EXPORT_ADDR: 
                TVPInitImportStub(reinterpret_cast<iTVPFunctionExporter *>(req.expaddr()));
                send_res(responder, res);
                break;
            case xp3::Request::INIT_PNG_PLUGIN:
                // todo: add png dll handle
                send_res(responder, res);
                break;
            case xp3::Request::EXRACT_FILE: {
                std::string desc("succeed");
                int ret_val = 0;
                for (int i = 0; ret_val == 0 && i < req.filetoextract_size(); ++i) {
                    ret_val = extract_file(req.extractpath().c_str(), // save path
                                            req.filetoextract(i).c_str(),
                                            desc); // file to extract
                }
                res.set_retval(ret_val);
                res.set_description(desc);
                send_res(responder, res);
            }
                break;
            case xp3::Request::ALLOC_CONSOLE:
                make_console();
                break;
            default:
                res.set_retval(1);
                send_res(responder, res);
                break;
            }
        } else {
            exit(0);
        }
    }
    return 0;
}
