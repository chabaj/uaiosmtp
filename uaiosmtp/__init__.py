from functools import partial
import uaiosmtp.tls
from .command import command, Command, UnexpectedCommand
from .reply import reply

@command('VRFY')
class Verify(Command):
    pass


@command('EXPN')
class Expand(Command):
    pass


address_literal = '(?:\[(?:(?:\d{1,3}(?:\.\d{1,3}){3})|(?:IPv6:.*?))\])'
fqdn = '(?:\w+(?:\.\w+)*)'
address = '(?:' + fqdn + '|' + address_literal + ')'

@command('HELO\s+(?P<address>' + address + ')')
class HELO(Command):
    def __init__(self, address):
        self.address = address

    def __iter__(self, address):
        yield self.address

@command('EHLO\s+(?P<address>' + address + ')')
class EHLO(Command):
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


@command('HELP')
class Help(Command):
    pass


@command('QUIT')
class Quit(Command):
    pass


async def rcpt_tos(reader):
    while True:
        try:
            receiver = await RcptTo.read(reader)
            yield receiver.address
        except UnexpectedCommand as ue:
            if not isinstance(ue.command, Data):
                raise
            else:
                break

class NoTerminationCondition(Exception):
    pass

async def data(reply, reader):
    read = await reader.readuntil(b'\r\n.\r\n')
    return read

async def serve(session, fqdn, ssl_context, reader, writer):
    _reply = partial(reply, writer)
    await _reply(220, fqdn)

    try:
        client_address, = await EHLO.read(reader)
        await _reply(250, b' '.join((fqdn, b'entertain me')), b'STARTTLS')
    except UnexpectedCommand as ue:
        if isinstance(ue.command, HELO):
            await _reply(520, b' '.join((fqdn, b'require STARTTLS so greet with EHLO')))
        else:
            await _reply('520', repr(e).encode('utf8'))
        writer.close()
        return
    except Exception as e:
        await _reply('520', repr(e).encode('utf8'))
        writer.close()
        return

    try:
        await StartTLS.read(reader)
        await _reply(220, b'Go ahead')
    except UnexpectedCommand as ue:
        await _reply(530, b'A STARTTLS command was expected :(')
        writer.close()
        return
    
    await writer.start_tls(ssl_context, server_hostname=fqdn)
    
    client_address, = await Command.read(reader, [EHLO, HELO])
    
    await _reply(250, b' '.join((fqdn, b'entertain me')))
    
        
    try:
        while True:
            await session(partial(MailFrom.read, reader),
                          partial(rcpt_tos, reader),
                          partial(data, _reply, reader),
                          _reply)
    except UnexpectedCommand as ue:
        if not isinstance(ue.command, Quit):
            await _reply('520', repr(ue).encode('utf8'))
        else:
            await _reply(221, b'Close connection')
    except Exception as e:
        await _reply('520', repr(e).encode('utf8'))
    writer.close()

def Server(session, fqdn, ssl_context=None):
    if isinstance(fqdn, str):
        fqdn = fqdn.encode('utf-8')
    return partial(serve, session, fqdn, ssl_context)
    
