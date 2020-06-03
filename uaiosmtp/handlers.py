from random import choice
from string import ascii_letters as letters
from .command import Expand, Verify
from os import symlink, makedirs

def filename_generator():
    return ''.join([choice(letters)
                    for _
                    in range(20)]) + '.mail'

async def store_mail_and_link_for_user(path, addresses, mail_from, rcpt_tos, data, reply):
    sender = await mail_from()
    await reply(250, b'Ok')

    users = set()
    async for receiver in rcpt_tos():
        local_user = receiver in addresses.values()
        if local_user:
            users |= {receiver}
        
        if local_user:
            await reply(250, b'Ok')
        else:
            await reply(551, 'User is not local ! try to ask {}'.format(receiver.split('@')[1]).encode('utf-8'))

    if any(users):
        await reply(354,b'End data with \\r\\n.\\r\\n')

        filename = filename_generator()
        with open(path + '/' + filename,
                  'wb') as f:
            f.write(await data())
            for user in users:
                makedirs(path + '/' + user, exist_ok=True)
                symlink(path + '/' + filename,
                        path + '/' + user + '/' + filename)
        await reply(250, b'Ok')
    else:
        await reply(551, b'not even one receiver was a localy registed user')

async def identify_from_dictionaries(adresses, lists, reply, command):
    if isinstance(command, Expand):
        if command.list in lists.keys():
            await reply(250, *lists[command.list])
        else:
            await reply(550, 'no such mail list')
    elif isinstance(command, Verify):
        mathcing_addresses = [name + ' <' + address + '>'
                              for name, address in addresses.items()
                              if command.address in address]
        if len(matching_addresses) > 0:
            if len(matching_addresses) == 1:
                await reply(250, *matching_addresses)
            else:
                await reply(553, 'Given entry is ambiguous:', *matching_addresses)
        else:
            await reply(550, 'no such mail address')
    else:
        raise Exception('Something is fishy')
