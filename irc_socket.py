import socket
import threading
from Event import Event
from Message import Message, ParseError

class IRCSocket:
    def __init__(self, ip, port, nick, realname, username, event_callback) -> None:
        self.ip = ip
        self.port = port
        self.nick = nick
        self.realname = realname
        self.username = username
        self.event_callback = event_callback
        self.socket = None
        self.running = False

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip, self.port))

        self.socket.send(f"USER {self.username} 0 * :{self.realname}\r\n".encode("utf-8"))
        self.socket.send(f"nick {self.nick}\r\n".encode("utf-8"))

        self.running = True
        threading.Thread(target=self._receive_messages, daemon=True).start()

    def _receive_messages(self) -> None:
        while self.running:
            if not self.socket:
                self.running = False
                raise ConnectionError("IRC Socket is not initialized")
            try:
                response = self.socket.recv(2048).decode("utf-8", errors="ignore")
                if not response:
                    print("Disconnected from server.")
                    break

                lines = response.strip().split("\r\n")
                for line in lines:
                    if line.startswith("PING"):
                        pong_response = "PONG " + line.split()[1] + "\r\n"
                        self.socket.send(pong_response.encode("utf-8"))
                    else:
                        msg = Message.from_irc(line)
                        event = Event(
                        type="irc_message",
                        data={"message": msg})
                        self.event_callback(event)
            except ParseError as e:
                print(f"Error: {e}")
                continue
            except Exception as e:
                print(f"Error: {e}")
                break

    def send_message(self, message: Message) -> None:
        if not self.socket:
            self.running = False
            raise ConnectionError("IRC Socket is not initialized")
        try: 
            self.socket.send((f"{message.command} {message.middle_params} {message.trailing}" + "\r\n").encode("utf-8"))
        except Exception as e:
            print(e)

    def close(self):
        self.running = False
        try:
            self.socket.close()
        except Exception as e:
            print(e)
