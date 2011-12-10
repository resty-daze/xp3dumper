#include "zmq_wrapper.h"
#include <zmq.h>

bool recv_req(void* sock, xp3::Request &req) {
    zmq_msg_t request;
    zmq_msg_init (&request);
    zmq_recv (sock, &request, 0);
    int size = zmq_msg_size (&request);
    bool ret = req.ParseFromArray(zmq_msg_data(&request), size);
    zmq_msg_close (&request);
    return ret;
}

bool send_res(void* sock, const xp3::Response & res) {
    zmq_msg_t reply;
    int size = res.ByteSize();
    zmq_msg_init_size(&reply, size);
    res.SerializeToArray(zmq_msg_data(&reply), size);
    zmq_send(sock, &reply, 0);
    zmq_msg_close(&reply);
}

void* rep_sock(const char* addr) {
    static void *context = zmq_init(1);
	void * sock = zmq_socket (context, ZMQ_REP);
	zmq_bind (sock, addr);
}