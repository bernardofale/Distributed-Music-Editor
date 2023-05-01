"""CD Chat server program."""
import logging
import select
import socket
import selectors
from .protocol import CDProto, TextMessage, JoinMessage, RegisterMessage

logging.basicConfig(filename="server.log", level=logging.DEBUG)


class Server:
    """Chat Server process."""
    def __init__(self):
        
        #sockets configs
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.bind(('localhost', 6003))

        #self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serversocket.listen(100)
        logging.info("Server socket is online.")

        #selector variables
        self.sel = selectors.DefaultSelector()
        
        #Need to keep a list of the channels of each client and connected clients
        self.cli_dict = {}

    def loop(self):
        """Loop indefinetely."""
        
        #Register the server socket
        self.sel.register(self.serversocket, selectors.EVENT_READ, self.accept_cli)

        #Main loop -> Loop for occurances in the registered events
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
        

    def accept_cli(self, sock, mask):

        #Accept client socket and set to non-blocking when there's an occurance in the server socket 
        conn, addr = sock.accept()  
        logging.info(f'Client socket connected from {addr}.')
        conn.setblocking(False)

        #Register the client socket
        self.sel.register(conn, selectors.EVENT_READ, self.handle)
        
    def handle(self, conn: socket, mask):

        #Receive the message through protocol so it can be processed and sent away
        data = CDProto.recv_msg(conn)
        
        #If there's data process it considering its type, else it means that the connection is closed
        if data:
            logging.info(f'Received {data} from {conn.getpeername()}')
            if isinstance(data, TextMessage):
                data_channel = data.channel if 'channel' in data.mydict else None
                for cli, channel in self.cli_dict.items():
                    if channel == data_channel:
                        CDProto.send_msg(cli, data)
                        logging.info(f'Sent {data} to client {cli.getpeername()} on channel {data_channel}.')
            elif isinstance(data, RegisterMessage):
                self.cli_dict[conn] = None
                logging.info(f'Client {conn.getpeername()} registered as {data.username}.')
            elif isinstance(data, JoinMessage):
                #Add the channel to the client dict
                self.cli_dict[conn] = data.channel
                logging.info(f'Client {conn.getpeername()} joined channel {data.channel}.')
        else:    
            #Remove client from connections dictionary, unregister and close socket
            logging.info(f'Closing client socket {conn}')
            self.cli_dict.pop(conn)
            self.sel.unregister(conn)
            conn.close()
