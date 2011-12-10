#include <windows.h>
#include <zmq.h>
#include "xp3proto.pb.h"

static bool recv_req(void* sock, xp3::Request &req) {
    zmq_msg_t request;
    zmq_msg_init (&request);
    zmq_recv (sock, &request, 0);
    int size = zmq_msg_size (&request);
    bool ret = req.ParseFromArray(zmq_msg_data(&request), size);
    zmq_msg_close (&request);
    return ret;
}

static bool send_res(void* sock, const xp3::Response & res) {
    zmq_msg_t reply;
    int size = res.ByteSize();
    zmq_msg_init_size(&reply, size);
    res.SerializeToArray(zmq_msg_data(&reply), size);
    zmq_send(sock, &reply, 0);
    zmq_msg_close(&reply);
}

extern "C" HRESULT _stdcall V2Link(DWORD exporter) {
    void *context = zmq_init (1);
    // Socket to talk to clients
    void *responder = zmq_socket (context, ZMQ_REP);
    zmq_bind (responder, "tcp://*:10010");
    
    while (1) {
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
    // We never get here but if we did, this would be how we end
    zmq_close (responder);
    zmq_term (context);
    return S_OK;
}
extern "C" HRESULT _stdcall V2Unlink() {
    return S_OK;
}
