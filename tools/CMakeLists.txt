set(CMAKE_SHARED_LIBRARY_SUFFIX "")
set(CMAKE_SHARED_LIBRARY_PREFIX "")



# Protobuf File:
set(pb_src_dir ${PROJECT_SOURCE_DIR}/proto)
add_custom_command(OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/xp3proto.pb.cc
                   COMMAND protoc -I=${pb_src_dir} --cpp_out=${CMAKE_CURRENT_BINARY_DIR} ${pb_src_dir}/xp3proto.proto
				   DEPENDS ${pb_src_dir}/xp3proto.proto)
include_directories(${CMAKE_CURRENT_BINARY_DIR})

# !get_addr.tpm
add_library(!get_addr.tpm SHARED tp_plugin.def get_addr.cpp zmq_wrapper.cpp ${CMAKE_CURRENT_BINARY_DIR}/xp3proto.pb.cc)
target_link_libraries(!get_addr.tpm protobuf-lite zmq)

# dllinject
add_executable(dllinject dllinject.cpp)

# dumper.dll
add_library(dumper.dll SHARED dumper.cpp stub/tp_stub.cpp zmq_wrapper.cpp ${CMAKE_CURRENT_BINARY_DIR}/xp3proto.pb.cc)
target_link_libraries(dumper.dll protobuf-lite zmq)
