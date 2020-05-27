from asyncio import get_event_loop, start_server
from uaiosmtp import Server
from functools import partial
from random import choice
from string import ascii_letters as letters

def filename_generator():
    return ''.join([choice(letters)
                    for _
                    in range(20)]) + '.mail'

async def mail(path, mail_from, rcpt_tos, data, reply):
    sender = await mail_from()
    await reply(250, b'Ok')

    at_least_one_local_user = False
    async for receiver in rcpt_tos():
        local_user = receiver.endswith('@kraamut.cz')
        at_least_one_local_user |= local_user
        
        if local_user:
            await reply(250, b'Ok')
        else:
            await reply(551, 'User not local try to ask {}'.format(receiver.split('@')[1]).encode('utf-8'))

    if at_least_one_local_user:
        await reply(354,b'End data with \\r\\n.\\r\\n')
        
        with open(path + '/' + filename_generator(),
                  'wb') as f:
            f.write(await data())
        
        await reply(250, b'Ok')
    else:
        await reply(551, b'not even one receiver was a localy registed user')
        return

from sys import argv
import ssl

storage_path, binding_address, port, fqdn, certfile, keyfile = argv[1:]

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile=certfile, keyfile=keyfile)

loop = get_event_loop()

loop.run_until_complete(start_server(Server(partial(mail, storage_path), fqdn, context), binding_address, int(port)))

loop.run_forever()
