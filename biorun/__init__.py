import os

VERSION = "0.0.7"

#
# Turn off broken pipe errors that may appear when piping into unix tools (head/tail etc)
#
# https://stackoverflow.com/questions/14207708/ioerror-errno-32-broken-pipe-python/30091579#30091579
#
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE, SIG_DFL)