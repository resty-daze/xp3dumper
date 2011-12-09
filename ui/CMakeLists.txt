set(ui_src_dir ${PROJECT_SOURCE_DIR}/ui)
set(pb_src_dir ${PROJECT_SOURCE_DIR}/proto)

file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/ui-dist)

add_custom_target(ui_target ALL 
                  DEPENDS ui-dist/ui.exe)

add_custom_command(OUTPUT ui-dist/ui.exe
                   COMMAND python ${ui_src_dir}/setup.py py2exe
                   DEPENDS setup.py ui.py xp3start.py ${ui_src_dir}/xp3proto_pb2.py)

add_custom_command(OUTPUT ${ui_src_dir}/xp3proto_pb2.py
                   COMMAND protoc -I=${pb_src_dir} --python_out=${ui_src_dir} ${pb_src_dir}/xp3proto.proto)
				   
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/build_conf.py src_dir=\"${ui_src_dir}\" )
