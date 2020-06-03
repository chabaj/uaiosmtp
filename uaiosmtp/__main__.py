from asyncio import get_event_loop, start_server
from uaiosmtp import Server
from functools import partial
from sys import argv
import ssl
from uaiosmtp.handlers import identify_from_dictionaries, store_mail_and_link_for_user

storage_path, binding_address, port, fqdn, certfile, keyfile = argv[1:]

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile=certfile, keyfile=keyfile)

loop = get_event_loop()

loop.run_until_complete(start_server(Server(partial(store_mail_and_link_for_user, storage_path, {}),
                                            fqdn,
                                            partial(identify_from_dictionaries, {}, {}),
                                            context),
                                     binding_address,
                                     int(port)))

loop.run_forever()
