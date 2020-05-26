from re import compile, IGNORECASE

class MalformedCommand(Exception):
    def __init__(self, line):
        self.line = line

    def __repr__(self):
        return 'received {} but unable to make sense of it'.format(self.line)


class UnexpectedCommand(Exception):
    def __init__(self, command, expected):
        self.command = command
        self.expected = expected

    def __repr__(self):
        return 'received {} while expeceting {}'.format(self.command, self.expected)


class Command:
    Commands = set()
    rule = None

    @classmethod
    def match(cls, line):
        match = cls.rule.match(line)
        
        if match is None:
            return
        
        groups = match.groups()
        return cls(*groups)

    
    @classmethod
    async def read(cls, reader, Commands=None):
        line = await reader.readuntil(b'\r\n')
        line = line[:-2].decode('utf-8')
        
        if cls.rule is None:
            if Commands is not None:
                for Command in Commands:
                    command = Command.match(line)

                    if command is not None:
                        return command
        else:
            command = cls.match(line)

            if command is not None:
                return command

        for Command in cls.Commands:
            command = Command.match(line)
            
            if command is not None:
                raise UnexpectedCommand(command, Command)
        
        raise MalformedCommand(line)

def command(rule):
    rule = compile('\s*' + rule + '\s*', IGNORECASE)
    
    def decorator(cls):
        Command.Commands |= {cls}
        setattr(cls, 'rule', rule)
        return cls

    return decorator
