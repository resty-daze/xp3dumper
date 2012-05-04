#include <cstdio>
#include <sstream>
#include <windows.h>
#include "zmq_wrapper.h"
#include "stub/tp_stub.h"

using namespace std;

const int kPathLen = 1024;
const int kDummyCutCount = 8 * 1024;
bool png_dummy_cut = false;

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
static bool use_png = false;

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

std::wstring format_path(const wchar_t * path) {
    if (memcmp(path, L"file:", 10)==0) {
        return path;
    } else if (path[1] == L':' && ( path[0] <= L'Z' && path[0] >= L'A' ||  path[0] <=L'z' && path[0] >= L'a')) {
        wstring res(L"file://./");
        res += path[0];
        unsigned int i;
        for (i = 2; path[i]!=0; ++i) {
            if (path[i] == '\\') {
                res += '/';
            } else {
                res += path[i];
            }
        }
        return res;
    } else {
        unsigned int i, flag = 0;
        for (i = 0; path[i] != 0; ++i) {
            if (path[i] == '/' || path[i] =='\\' || path[i] =='*') {
                flag = 1;
                break;
            }
        }
        if (!flag) {
            wchar_t * buffer = new wchar_t [512];
            GetCurrentDirectoryW( 512 , buffer );
            wstring res = format_path((wstring(buffer) + L'/' + path).c_str());
            delete [] buffer;
            return res;
        }
    }
    return L"";
}
/// extract a file
static int extract_file(int id, int total,
                        const char * path, // path to save, (utf-8)
                        const char * name, // file to save, (utf-8)
                        string & desc) {   // error description
    wchar_t wpath[kPathLen];
    wchar_t wname[kPathLen];
    MultiByteToWideChar(CP_UTF8, 0, path, strlen(path) + 1, wpath, sizeof(wpath));
    MultiByteToWideChar(CP_UTF8, 0, name, strlen(name) + 1, wname, sizeof(wname));

    HANDLE hConsole = GetStdHandle(STD_OUTPUT_HANDLE);
    printf("[");
    SetConsoleTextAttribute( hConsole, FOREGROUND_BLUE | FOREGROUND_GREEN );
    printf("%5d/%d", id, total);
    SetConsoleTextAttribute( hConsole, FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_RED);
    wprintf(L"]\t%s\n", wname);
    int len = strlen(name);
    if (use_png &&
        len > 3 &&
        name[len-3]=='t' &&
        name[len-2]=='l' &&
        name[len-1]=='g' ) {
        void SaveTLGToPng(const wchar_t * filename, const wchar_t * path);
        wstring png_path(wpath);
        png_path += L"/";
        png_path += wname;
        int l = png_path.size();
        png_path[l-3] = L'p';
        png_path[l-2] = L'n';
        png_path[l-1] = L'g';
        SaveTLGToPng(wname, format_path(png_path.c_str()).c_str());
        return 0;
    }

    bool dummy_cut = png_dummy_cut &&
        len > 3 &&
        name[len-3] == 'p' &&
        name[len-2] == 'n' &&
        name[len-1] == 'g';
    
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
    unsigned int last_eql_cnt = 0;
    char last_char = 0;
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
        if (dummy_cut) {
            for (int i = 0; i < size; ++i)
                if (buffer[i] != last_char) {
                    last_eql_cnt = 1;
                    last_char = buffer[i];
                } else {
                    ++ last_eql_cnt;
                }
            if (last_eql_cnt >= kDummyCutCount)
                break;
        }
    }
    return 0;
}


static int init_png_dll(const string & path, string & desc) {
    if (use_png) {
        desc = "Error: init more than once.";
        return 1;
    }

    wchar_t wpath[kPathLen];
    MultiByteToWideChar(CP_UTF8, 0, path.c_str(), path.size()+1, wpath, sizeof(wpath));
    
    HMODULE hModule = LoadLibraryW(wpath);
    if (hModule == NULL) {
        desc = "Error: failed load dll";
        return 2;
    }
    typedef HRESULT (_stdcall *tlink)(iTVPFunctionExporter *);
    tlink v2link = (tlink)GetProcAddress(hModule, "V2Link");
    wprintf(L"PngDLL : V2Link = 0x%x", v2link);
    extern iTVPFunctionExporter * TVPFunctionExporter;
    v2link(TVPFunctionExporter);

    // prepare for dump tlg
    TVPExecuteScript(ttstr(L"var tmpW_xp3=new Window();"));
    TVPExecuteScript(ttstr(L"var tmpLayer=new Layer(tmpW_xp3, null);"));
    TVPExecuteScript(ttstr(L"tmpLayer.opacity=255;"));
    use_png = true;
    return 0;
}

void SaveTLGToPng(const wchar_t * filename, const wchar_t * path) {
    const wstring ConstU = L"tmpLayer.saveLayerImagePng(\"";
    wstring str, fname = filename;
    str = L"tmpLayer.loadImages(\""+ fname + L"\");";
    TVPExecuteScript(ttstr(str.c_str()));
    TVPExecuteScript(ttstr(L"tmpLayer.setSizeToImageSize();"));
    str = ConstU + wstring(path) + L"\");";
    TVPExecuteScript(ttstr(str.c_str()));
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
            case xp3::Request::INIT_PNG_PLUGIN: {
                printf("init PNG DLL.\n");
                std::string desc("succeed");
                int ret_val = init_png_dll(req.pngpluginpath(), desc);
                res.set_retval(ret_val);
                res.set_description(desc);
                send_res(responder, res);
            }
                break;
            case xp3::Request::EXTRACT_FILE: {
                std::string desc("succeed");
                int ret_val = 0;
                int size = req.filetoextract_size();
                for (int i = 0; ret_val == 0 && i < size; ++i) {
                    ret_val = extract_file(i + 1,
                                           size,
                                           req.extractpath().c_str(), // save path
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
                send_res(responder, res);
                break;
            case xp3::Request::PNG_DUMMY_CUT:
                printf("enable dummy cut\n");
                png_dummy_cut = true;
                send_res(responder, res);
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
