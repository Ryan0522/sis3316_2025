SERVER_ID = b'sis3316'  # Name of sis3316 zmq server
PLOTTER_ID = b'livePlotter' # Name of the live plotter zmq server
IP_ADDRESS = '192.17.208.78' # sis3316 IP address
TCP_SOCKET = 5560       # Socket for zmq DEALER/ROUTER
PUSH_SOCKET = 5559      # Socket for zmq PUSH from server to status monitor
OUTHEAD = 'ch' # sis3316 binary output filename starts with this
OUTEXT = '.dat' # output extension name
ATTR_FILE = 'attr.txt' # Run attribute file
