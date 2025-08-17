import argparse
from Message import Message
from irc_socket import establish_socket, send_message

LOGGING = True

def main(ip, port, nick, realname, username):
    irc_socket = establish_socket(ip, port, nick, realname, username, LOGGING)
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

