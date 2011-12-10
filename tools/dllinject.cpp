// Helper tool : Inject Dll to specific process

#include <cstring>
#include <cstdio>
#include <windows.h>

static void print_help() {
    fprintf(stderr, "dllinject -- a simple cmdline dll injector tool\n"
            "Usage:\n"
            "dllinject remote dllname pid\n");
}

static int do_remote(const char * dll_name, DWORD pid) {
    HANDLE hProcess = OpenProcess(PROCESS_ALL_ACCESS,0,pid);
    if (hProcess == 0) {
        fprintf(stderr, "failed open process: %u", pid);
        return 127;
    }
    
    LPVOID remoteFile = VirtualAllocEx(hProcess,
                                       NULL,
                                       strlen(dll_name) + 5,
                                       MEM_COMMIT, PAGE_READWRITE);
    if (remoteFile == NULL) {
        fprintf(stderr, "failed alloc remote space");
        return 2;
    }

    if (!WriteProcessMemory(hProcess,
                            remoteFile,
                            dll_name,
                            strlen(dll_name) + 1,
                            NULL)) {
        fprintf(stderr, "failed write remote process");
        return 3;
    }
    
    LPTHREAD_START_ROUTINE pfnThreadRtn =
        reinterpret_cast<LPTHREAD_START_ROUTINE>(GetProcAddress(GetModuleHandle("Kernel32.dll"),
                                                          "LoadLibraryA")); 
    if (pfnThreadRtn == NULL) {
        fprintf(stderr, "failed get kernel32.LoadLibraryA address");
        return 4;
    }

    HANDLE hThread = CreateRemoteThread(hProcess,
                                        NULL,
                                        0,
                                        pfnThreadRtn, // LoadLibrary地址
                                        remoteFile, // 要加载的DLL名
                                        0,
                                        NULL);
    if (hThread == 0) {
        fprintf(stderr, "failed create remote thread");
        return 5;
    }
    
    return 0;
}

int main(int argc, char ** argv) {
    if (argc < 3) {
        print_help();
        return 1;
    }
    if (strcmp(argv[1], "remote")==0) {
        if (argc < 4) {
            print_help();
            return 1;
        }
        return do_remote(argv[2], static_cast<DWORD>(atoi(argv[3])));
    } else {
        fprintf(stderr, "Error: Unknown mode [%s]", argv[1]);
        return 1;
    }
    return 0;
}
