import socket
from sqlite3 import DatabaseError
import threading
from Event import Event
from Message import Message, ParseError

def receive_messages(irc_socket, lain) -> None:
    while True:
        try:
            response = irc_socket.recv(2048).decode("utf-8", errors="ignore")
            if not response:
                print("Disconnected from server.")
                break

            lines = response.strip().split("\r\n")
            for line in lines:
                if line.startswith("PING"):
                    pong_response = "PONG " + line.split()[1] + "\r\n"
                    irc_socket.send(pong_response.encode("utf-8"))
                else:
                    msg = Message.from_irc(line)
                    event = Event(
                    type="irc_message",
                    data={"message": msg})
                    lain.create_event(event)
        except ParseError as e:
            print(f"Error: {e}")
            continue
        except Exception as e:
            print(f"Error: {e}")
            break

def establish_socket(ip, port, nick, realname, username, lain, logging=True) -> socket.socket:
    irc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    irc_socket.connect((ip, port))
    
    irc_socket.send(f"USER {username} 0 * :{realname}\r\n".encode("utf-8"))
    irc_socket.send(f"nick {nick}\r\n".encode("utf-8"))
    
    threading.Thread(target=receive_messages, args=(irc_socket, lain,), daemon=True).start()
    return irc_socket

def send_message(socket: socket.socket, message: Message) -> None:
    try: 
        socket.send((f"{message.command} {message.middle_params} {message.trailing}" + "\r\n").encode("utf-8"))
    except Exception as e:
        print(e)
