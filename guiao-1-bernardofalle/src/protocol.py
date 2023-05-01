"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
from datetime import datetime
import selectors
from socket import socket, error


class Message:
    """Message Type."""
    def __init__(self, command) -> None:
        self.mydict = {
            "command" : command
        }
    def __str__(self) -> str:
        return json.dumps(self.mydict)
    
    def msg(self):
        return json.dumps(self.mydict)

    
class JoinMessage(Message):
    """Message to join a chat channel.
    { "command" : "join",
              "channel" : "#cd" } """
    
    def __init__(self, channel):
        super().__init__('join')
        self.channel = channel
    
    
    
    def update(self):
        dict = {
            "channel" : self.channel
        }
        self.mydict.update(dict)

class RegisterMessage(Message):
    """Message to register username in the server.
    { "command" : "register",
              "user" : "student" } """
    
    def __init__(self, username):
        super().__init__('register')
        self.username = username

    
    def update(self):
        dict = {
            "user" : self.username
        }
        self.mydict.update(dict)

class TextMessage(Message):
    """Message to chat with other clients.
    { "command" : "message",
          "message" : "Hello World",
          "channel" : "#cd",
          "ts" : 1615852800 } """
    
    def __init__(self, message, channel):
        super().__init__('message')
        self.message = message
        self.channel = channel


    def update(self):
        tm = datetime.now()
        ts = int(tm.timestamp())
        if self.channel:
            dict = {
                "message" : self.message,
                "channel" : self.channel,
                "ts" : ts
            }
        else:
            dict = {
                "message" : self.message,
                "ts" : ts
            }

        self.mydict.update(dict)

class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object. """
        reg_msg = RegisterMessage(username)
        reg_msg.update()
        return reg_msg

    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object. """
        join_msg = JoinMessage(channel)
        join_msg.update()
        return join_msg
        

    @classmethod
    def message(cls, message: str, channel: str = None) -> TextMessage:
        """Creates a TextMessage object. """
        text_msg = TextMessage(message, channel)
        text_msg.update()
        return text_msg
    
    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""
        json_msg = msg.msg().encode(encoding="utf-8")
        msg_length = len(json_msg)
        length_in_bytes = msg_length.to_bytes(2, byteorder='big')
        connection.sendall(length_in_bytes+json_msg)
        
    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""
        #Reads the message length and decodes it
        try:
            length = connection.recv(2)
            msglen = int.from_bytes(length, byteorder='big')
            #Reads the message data 
            msg = connection.recv(msglen).decode(encoding="utf-8")
        except error:
            return        
        
        #If there's no data on the network buffer the connection is closed
        if not msg:
            return
        
        #If the message is not in json then it must not be sent to the client(s)
        try:
            mydict = json.loads(msg)
        except json.JSONDecodeError:
            raise CDProtoBadFormat(f"Invalid message format: {msg}")
        
        #Return message based on its command
        if mydict['command'] == 'message':
            if 'channel' in mydict:
                m = CDProto.message(mydict['message'], mydict['channel'])
            else:
                m = CDProto.message(mydict['message'])
        elif mydict['command'] == 'join':
            m = CDProto.join(mydict['channel'])
        elif mydict['command'] == 'register':
            m = CDProto.register(mydict['user'])
        else:
            raise CDProtoBadFormat(f"{msg}")
        m.mydict = mydict   
        return m


class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")