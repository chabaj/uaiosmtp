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

    async def write(cls, writer):
        raise NotImplemented()
    
def command(rule):
    rule = compile('\s*' + rule + '\s*', IGNORECASE)
    
    def decorator(cls):
        Command.Commands |= {cls}
        setattr(cls, 'rule', rule)
        return cls

    return decorator

def expect(reader, *commands):
    return Command.read(reader, commands)

@command('VRFY\s+(?P<address>(?:[\w\.]+@[\w\.]+)|(?:[\w\s]+<[\w\.]+@[\w\.]+>))')
class Verify(Command):
    def __init__(self, address):
        self.address = address


@command('EXPN\s+(?<list>\w+(-\w+)*)')
class Expand(Command):
    def __init__(self, list):
        self.list = list


address_literal = '(?:\[(?:(?:\d{1,3}(?:\.\d{1,3}){3})|(?:IPv6:.*?))\])'
fqdn = '(?:\w+(?:\.\w+)*)'
address = '(?:' + fqdn + '|' + address_literal + ')'

@command('HELO\s+(?P<address>' + address + ')')
class Helo(Command):
    def __init__(self, address):
        self.address = address

    def __iter__(self, address):
        yield self.address


@command('EHLO\s+(?P<address>' + address + ')')
class Ehlo(Command):
    def __init__(self, address):
        self.address = address

    def __iter__(self):
        yield self.address


@command('STARTTLS')
class StartTLS(Command):
    pass


@command('MAIL\s+FROM\s*:\s*<\s*(?P<address>.*?)\s*>')
class MailFrom(Command):
    def __init__(self, address):
        self.address = address

    def __iter__(self):
        yield self.address


@command('RCPT\s+TO\s*:\s*<\s*(?P<address>.*)\s*?>')
class RcptTo(Command):
    def __init__(self, address):
        self.address = address

    def __iter__(self):
        yield self.address

@command('DATA')
class Data(Command):
    pass


@command('NOOP(?:\s+.*?)?')
class NoOp(Command):
    pass


@command('RSET')
class Reset(Command):
    pass


@command('HELP(?:\s+(?P<command>\w+))?')
class Help(Command):
    def __init__(self, command):
        self.command = command

    def __iter__(self):
        yield self.command

@command('QUIT')
class Quit(Command):
    pass
