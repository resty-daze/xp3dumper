#ifndef ZMQ_WRAPPER_H_
#define ZMQ_WRAPPER_H_

#include "xp3proto.pb.h"

bool recv_req(void* sock, xp3::Request &req);
bool send_res(void* sock, const xp3::Response & res);
void* rep_sock(const char* addr);

#endif
