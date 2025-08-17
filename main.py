import socket
import threading
import argparse
from Message import Message, ParseError

LOGGING = True

def receive_messages(irc_socket) -> None:
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
                    if LOGGING:
                        print(msg)
        except ParseError as e:
            print(f"Error: {e}")
            continue
        except Exception as e:
            print(f"Error: {e}")
            break

def establish_socket(ip, port, nick, realname, username) -> socket.socket:
    irc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    irc_socket.connect((ip, port))
    
    irc_socket.send(f"USER {username} 0 * :{realname}\r\n".encode("utf-8"))
    irc_socket.send(f"nick {nick}\r\n".encode("utf-8"))
    
    threading.Thread(target=receive_messages, args=(irc_socket,), daemon=True).start()
    return irc_socket

def send_message(socket: socket.socket, message: Message) -> None:
    socket.send((f"{message.command} {message.middle_params} {message.trailing}" + "\r\n").encode("utf-8"))

def main(ip, port, nick, realname, username):
    irc_socket = establish_socket(ip, port, nick, realname, username)
    try:
        while True:
            message = Message.from_command(input(), nick=nick, user=username)
            send_message(irc_socket, message)
            if message.command.lower() in ["quit", "exit"]:
                break
    except KeyboardInterrupt:
        send_message(irc_socket, Message.from_command("QUIT", nick=nick, user=username))
    finally:
        irc_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser('DeathStarBench social graph initializer.')
    parser.add_argument('--ip', help='IRC server\'s IP address', default='192.168.0.22')
    parser.add_argument('--port', help='IRC server\'s port', default=6667)
    parser.add_argument('--nick', help='IRC client\'s nick', default='Lain')
    parser.add_argument('--realname', help='IRC client\'s realname', default='And I am me.')
    parser.add_argument('--username', help='IRC client\'s username', default='lain')
    args = parser.parse_args()
    main(args.ip, args.port, args.nick, args.realname, args.username)

