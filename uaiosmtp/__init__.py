from functools import partial
import uaiosmtp.tls
from .reply import reply
from .command import (expect,
                      Command,
                      UnexpectedCommand,
                      Helo, Ehlo, StartTLS,
                      MailFrom, RcptTo,
                      Data,
                      Reset, Quit,
                      Verify, Expand, Help,
                      NoOp)

async def expect_potent(expect, reply, identify=None, *args, **kargs):
    try:
        value = await expect(*args, **kargs)
        return value
    except UnexpectedCommand as ue:
        if isinstance(ue.command, Help):
            await reply(250,
                        'The available commands are:',
                        *((Command.rule.pattern
                           .replace('\s+', ' ')
                           .replace('\s*', ''))
                          for Command
                          in Command.Commands))
        elif isinstance(ue.command, (Verify, Expand)):
            if identify is None:
                await identify(reply, ue.command)
            else:
                await reply(502, 'Not implemented')
        elif isinstance(ue.command, NoOp):
            await reply(250, 'OK')
        else:
            raise

async def rcpt_tos(expect):
    while True:
        try:
            receiver = await expect(RcptTo)
            yield receiver.address
        except UnexpectedCommand as ue:
            if not isinstance(ue.command, Data):
                raise
            else:
                break

async def data(reply, reader):
    read = await reader.readuntil(b'\r\n.\r\n')
    return read

async def serve(session, identify, fqdn, start_tls, expect, reply, data):
    await reply(220, fqdn)

    try:
        client_address, = await expect(Ehlo)
        await reply(250, b' '.join((fqdn, b'entertain me')), b'STARTTLS')
    except UnexpectedCommand as ue:
        if isinstance(ue.command, Helo):
            await reply(520, b' '.join((fqdn, b'require STARTTLS so greet with EHLO')))
        else:
            await reply('520', repr(e).encode('utf8'))
        return
    except Exception as e:
        await reply('520', repr(e).encode('utf8'))
        return

    try:
        await expect(StartTLS)
        await reply(220, b'Go ahead')
    except UnexpectedCommand as ue:
        await reply(530, b'A STARTTLS command was expected :(')
        return
    
    await start_tls()
    
    client_address, = await expect(Ehlo, Helo)
    
    await reply(250, b' '.join((fqdn, b'entertain me')))
    
    try:
        while True:
            try:
                await session(partial(expect, MailFrom),
                              partial(rcpt_tos, expect),
                              data,
                              reply)
            except UnexpectedCommand as ue:
                if isinstance(ue.command, Reset):
                    await reply(250, b'OK')
                else:
                    raise
    except UnexpectedCommand as ue:
        if not isinstance(ue.command, Quit):
            await reply('520', repr(ue).encode('utf8'))
        else:
            await reply(221, b'Close connection')
    except Exception as e:
        await reply('520', repr(e).encode('utf8'))

async def _serve(session, identify, fqdn, ssl_context, reader, writer):
    _reply = partial(reply, writer)
    _expect = partial(expect_potent, partial(expect, reader), _reply, identify)
    start_tls = partial(writer.start_tls, ssl_context, server_hostname=fqdn)
    
    try:
        await serve(session, identify,
                    fqdn,
                    start_tls,
                    _expect,
                    _reply,
                    partial(data, _reply, reader))
    finally:
        writer.close()
   
def Server(session, fqdn, identify=None, ssl_context=None):
    print(session, fqdn, identify, ssl_context)
    if isinstance(fqdn, str):
        fqdn = fqdn.encode('utf-8')
    return partial(_serve, session, identify, fqdn, ssl_context)
    
