#include <windows.h>
#include "zmq_wrapper.h"

extern "C" HRESULT _stdcall V2Link(DWORD exporter) {
    void *responder = rep_sock ("tcp://*:10010");
    
    while (true) {
        xp3::Request req;
        if (recv_req(responder, req)) {
            xp3::Response res;
            switch(req.type()) {
            case xp3::Request::EXIT:
                exit(0);
                break;
            case xp3::Request::GET_EXPORT_ADDR: 
                res.set_retval(0);
                res.set_expaddr(exporter);
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

    return S_OK;
}
extern "C" HRESULT _stdcall V2Unlink() {
    return S_OK;
}
