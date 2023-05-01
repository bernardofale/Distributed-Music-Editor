"""CD Chat client program"""
import logging
import sys
import socket
import fcntl
import os
import selectors

from .protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)


class Client:
    """Chat Client process."""

    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""

        #Initializing socket
        self.name = name
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logging.info(f'Client {self.name} socket is online.')

        # register event
        self.m_selector = selectors.DefaultSelector()
        self.m_selector.register(sys.stdin, selectors.EVENT_READ, self.got_keyboard_data)
        self.m_selector.register(self.client_socket, selectors.EVENT_READ, self.recv)

        #Protocol variables
        self.reg_msg = CDProto.register(self.name)

        #Channel list
        self.channel = None 
        
    def connect(self):
        """Connect to chat server and setup stdin flags."""
        
        # set sys.stdin non-blocking
        self.orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, self.orig_fl | os.O_NONBLOCK)

        #Establishes connection to server
        self.client_socket.connect(('localhost', 6003))
        self.client_socket.setblocking(False)
        CDProto.send_msg(self.client_socket, self.reg_msg)
        logging.info(f'Client {self.name} connected to server socket.')

    def loop(self):
        """Loop indefinetely."""

        #Main loop -> Waits for occurances on registered events
        while True:
            #sys.stdout.write('Type something and hit enter: ')
            sys.stdout.flush()
            events = self.m_selector.select()
            for k, mask in events:
                callback = k.data
                callback(k.fileobj)
            
            
    
    def recv(self, conn):

        #Receives message through protocol
        msg = CDProto.recv_msg(self.client_socket)
        if msg:
            print(msg.message)
            logging.info(f'Received {msg} from server.')
        
            
    # function to be called when enter is pressed
    def got_keyboard_data(self, stdin):
        for line in stdin:
            ph = line.split()
        if ph[0] == 'exit':
            logging.info(f'Client {self.name} socket closed.')
            self.client_socket.close()
            sys.exit(0)
        elif ph[0] == '/join':
            join_msg = CDProto.join(ph[1])
            CDProto.send_msg(self.client_socket, join_msg)
            if ph[1]:
                self.channel = ph[1]
            logging.info(f'Client is sending {join_msg.msg()} to the server.')
        else:
            msg = ' '.join(ph)
            text_msg = CDProto.message(msg, self.channel)
            CDProto.send_msg(self.client_socket, text_msg)
            logging.info(f'Client is sending {text_msg.msg()} to the server.')
