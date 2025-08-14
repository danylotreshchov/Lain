import socket
import threading
import argparse

def receive_messages(irc_socket):
    while True:
        try:
            response = irc_socket.recv(2048).decode("utf-8", errors="ignore")
            if not response:
                print("Disconnected from server.")
                break
            print(response.strip())

            if response.startswith("PING"):
                pong_response = "PONG " + response.split()[1] + "\r\n"
                irc_socket.send(pong_response.encode("utf-8"))
        except Exception as e:
            print(f"Error: {e}")
            break

def main(ip, port, nick, realname):
    irc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    irc_socket.connect((ip, port))
    
    irc_socket.send(f"nick {nick}\r\n".encode("utf-8"))
    irc_socket.send(f"USER {nick} 0 * :{realname}\r\n".encode("utf-8"))
    
    threading.Thread(target=receive_messages, args=(irc_socket,), daemon=True).start()

    try:
        while True:
            command = input()
            if command.lower() in ["quit", "exit"]:
                irc_socket.send("QUIT\r\n".encode("utf-8"))
                break
            irc_socket.send((command + "\r\n").encode("utf-8"))
    except KeyboardInterrupt:
        irc_socket.send("QUIT\r\n".encode("utf-8"))
    finally:
        irc_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser('DeathStarBench social graph initializer.')
    parser.add_argument('--ip', help='IRC server\'s IP address', default='192.168.0.22')
    parser.add_argument('--port', help='IRC server\'s port', default=6667)
    parser.add_argument('--nick', help='IRC client\'s nick', default='Lain')
    parser.add_argument('--realname', help='IRC client\'s realname', default='And I am me.')
    args = parser.parse_args()
    main(args.ip, args.port, args.nick, args.realname)

