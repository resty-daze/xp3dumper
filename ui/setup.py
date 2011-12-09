from distutils.core import setup
import py2exe
import sys

sys.path.append('.')

import build_conf

if len(sys.argv) == 1:
    sys.argv.append("py2exe")

setup(
	options={
                "py2exe":{
                        "unbuffered": True,
                        "optimize": 2,
                        "dist_dir": 'ui-dist',
                        "includes": ["zmq.utils.strtypes", "zmq.utils.jsonapi", "google.protobuf"]
                }
        }, 
    windows = ["%s/ui.py" % build_conf.src_dir],
    )
