import queue
import threading
import DB
from LLMInterface import LLMInterface
from Message import Message
from Event import Event
import irc_socket

class Lain:
    def __init__(self, ip, port, nick, realname, username, logging=True) -> None:
        self.event_queue = queue.Queue()
        self.running = True
        self.handlers = {}
        self.ip = ip
        self.port = port
        self.nick = nick
        self.realname = realname
        self.username = username
        self.logging = logging
        self.prompting_commands = ["JOIN", "PRIVMSG", "421"]

        self.irc_socket = None 
        self.llm_interface = None
        self.db = DB.Database()
        self.register_handler("irc_message", lambda e: self.handle_irc_message(e))
        self.register_handler("send_message", lambda e: self.handle_send_message(e))
        self.register_handler("llm_prompt", lambda e: self.handle_llm_prompt(e))
        self.register_handler("llm_response", lambda e: self.handle_llm_response(e))

    def register_handler(self, event_type, handler_func):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler_func)

    def create_event(self, event):
        self.event_queue.put(event)

    def event_loop(self):
        while self.running:
            try:
                event = self.event_queue.get(timeout=1)
            except queue.Empty:
                continue

            if event.type in self.handlers:
                for handler in self.handlers[event.type]:
                    # handler(event)
                    threading.Thread(target=handler, args=(event,), daemon=True).start()

    def start(self):
        self.irc_socket = self.start_irc_socket()
        self.llm_interface = LLMInterface(self.create_event)
        self.start_keyboard_listener()
        self.event_loop()

    def stop(self):
        self.running = False
        if not self.irc_socket:
            return
        try:
            self.irc_socket.close()
        except Exception as e:
            print(e)

    def handle_irc_message(self, event):
        msg = event.data["message"]
        if not msg:
            raise ValueError("Received IRC message event with no 'message' in event.data")
        self.db.add_message(message=msg)
        if self.logging:
            print(msg)
        llm_event = Event(
            type="llm_prompt",
            data={"trigger_msg": msg})
        self.create_event(llm_event)

    def handle_send_message(self, event):
        msg = event.data["message"]
        if not msg:
            raise ValueError("Received IRC message event with no 'message' in event.data")
        if not self.irc_socket:
            raise RuntimeError("IRC socket is not initialized or already closed")
        self.irc_socket.send_message(msg)
        self.db.add_message(message=msg)
        if self.logging:
            print(msg)

    def handle_llm_prompt(self, event):
        last_msg = event.data["trigger_msg"]
        if not last_msg:
            return
        if last_msg.command in self.prompting_commands:
            msg_history = self.db.get_message_history(context_window=30)
            self.llm_interface.generate_response(last_msg, msg_history)


    def handle_llm_response(self, event):
        msg = event.data["message"]
        print(msg)
        event = Event(
            type="send_message",
            data={"message": msg}
        )
        self.create_event(event)
    def start_irc_socket(self):
        sock = irc_socket.IRCSocket(self.ip, self.port, self.nick, self.realname, self.username, self.create_event)
        sock.connect()
        return sock

    def start_keyboard_listener(self):
        def keyboard_listener():
            while True:
                user_input = input()
                if not user_input.strip():
                    continue
                event = Event(
                    type="send_message",
                    data={"message": Message.from_command(user_input, nick=self.nick, user=self.username)}
                )
                self.create_event(event)

        threading.Thread(target=keyboard_listener, daemon=True).start()
