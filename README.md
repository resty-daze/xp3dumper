# xp3dumper

A simple xp3 file unpacker

## Build it your self

### Dependence

- `python 2.7` : language for ui
  - `wxPython` : ui library
  - `pyzmq` : zeromq binding for python
- `cmake` 
- `MinGW` : for C++ compiler, or use other (not test yet)
  - `libzmq` : zeromq c interface
  
### Build

Using MinGW:

    mkdir build
    cd build
    cmake .. -G "MinGW Makefiles"
    mingw32-make
    
Or you can just use cmake gui to generate project file, then use it to build the project.

You will get ui at `ui/ui-dist` path, and tools at `tools` path. Copy them to `ui/ui-dist` to let ui use.

