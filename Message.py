import json
import re

IRC_MSG_PATTERN = re.compile(r'^(?:@(?P<tags>[^\r\n ]*) +|())(?:[:](?P<nick>[^\s!@]+)(?:!(?P<user>[^\s@]+))?(?:@(?P<host>[^\s]+))? +|())(?P<command>[^\r\n ]+)(?: +(?P<middle_params>[^:\r\n ]+[^\r\n ]*(?: +[^:\r\n ]+[^\r\n ]*)*)|())?(?: +:(?P<trailing>[^\r\n]*)| +())?[\r\n]*$') 
COMMAND_MSG_PATTERN = re.compile(r'^(?P<command>[A-Za-z]+)(?: +(?P<middle_params>[^\s]+))?(?: +(?P<trailing>.*))?$')

class ParseError(Exception):
    pass

class Message:
    def __init__(self, tags = "", nick = "", user = "", host = "", command = "", middle_params = "", trailing = ""):
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
        if not match:
            raise ParseError(f"Couldn't parse {raw_line} into a message")    
        groups = match.groupdict()
        return cls(
            tags=str(groups.get("tags")),
            nick=str(groups.get("nick")),
            user=str(groups.get("user")),
            host=str(groups.get("host")),
            command=str(groups.get("command")),
            middle_params=str(groups.get("middle_params")),
            trailing=str(groups.get("trailing"))
        )

    @classmethod
    def from_command(cls, raw_line, tags = "", nick = "", user = "", host = "localhost"):
        raw_line = raw_line.strip()
        match = COMMAND_MSG_PATTERN.match(raw_line)
        if not match:
            raise ParseError(f"Command \"{raw_line}\" couldn't be parsed into Message")
        groups = match.groupdict()
        return cls(
            tags=tags,
            nick=nick,
            user=user,
            host=host,
            command=str(groups.get("command")),
            middle_params=str(groups.get("middle_params")),
            trailing=str(groups.get("trailing"))
        )

    def __str__(self) -> str:
        return json.dumps({
            "tags": self.tags,
            "nick": self.nick,
            "user": self.user,
            "host": self.host,
            "command": self.command,
            "middle_params": self.middle_params,
            "trailing": self.trailing
        }, ensure_ascii=False)
