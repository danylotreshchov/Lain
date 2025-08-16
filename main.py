import socket
import json
import threading
import argparse
import re

LOGGING = True
IRC_MSG_PATTERN = re.compile(r'^(?:@(?P<tags>[^\r\n ]*) +|())(?:[:](?P<nick>[^\s!@]+)(?:!(?P<user>[^\s@]+))?(?:@(?P<host>[^\s]+))? +|())(?P<command>[^\r\n ]+)(?: +(?P<middle_params>[^:\r\n ]+[^\r\n ]*(?: +[^:\r\n ]+[^\r\n ]*)*)|())?(?: +:(?P<trailing>[^\r\n]*)| +())?[\r\n]*$') 


class Message:
    def __init__(self, tags, nick, user, host, command, middle_params, trailing):
        self.tags = tags 
        self.nick = nick
        self.user = user
        self.host = host
        self.command = command
        self.middle_params = middle_params
        self.trailing = trailing

    @classmethod
    def from_irc(cls, raw_line):
        raw_line = raw_line.strip()
        match = IRC_MSG_PATTERN.match(raw_line)
        if match:
            groups = match.groupdict()
            return cls(
                tags=groups.get("tags"),
                nick=groups.get("nick"),
                user=groups.get("user"),
                host=groups.get("host"),
                command=groups.get("command"),
                middle_params=groups.get("middle_params"),
                trailing=groups.get("trailing")
            )
        return None

    def __str__(self):
        return json.dumps({
            "tags": self.tags,
            "nick": self.nick,
            "user": self.user,
            "host": self.host,
            "command": self.command,
            "middle_params": self.middle_params,
            "trailing": self.trailing
        }, ensure_ascii=False)

def receive_messages(irc_socket):
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
        except Exception as e:
            print(f"Error: {e}")
            break

def main(ip, port, nick, realname, username):
    irc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    irc_socket.connect((ip, port))
    
    irc_socket.send(f"USER {username} 0 * :{realname}\r\n".encode("utf-8"))
    irc_socket.send(f"nick {nick}\r\n".encode("utf-8"))
    
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
    parser.add_argument('--username', help='IRC client\'s username', default='lain')
    args = parser.parse_args()
    main(args.ip, args.port, args.nick, args.realname, args.username)

