from asyncio.streams import StreamWriter, StreamReaderProtocol

def _replace_writer(self, writer):
    loop = self._loop
    transport = writer.transport
    self._stream_writer = writer
    self._transport = transport
    self._over_ssl = transport.get_extra_info('sslcontext') is not None


async def start_tls(self, sslcontext, *,
                    server_hostname=None,
                    ssl_handshake_timeout=None):
    """Upgrade an existing stream-based connection to TLS."""
    server_side = self._protocol._client_connected_cb is not None
    protocol = self._protocol
    await self.drain()
    new_transport = await self._loop.start_tls(  # type: ignore
        self._transport, protocol, sslcontext,
        server_side=server_side, server_hostname=server_hostname,
        ssl_handshake_timeout=ssl_handshake_timeout)
    self._transport = new_transport
    protocol._replace_writer(self)


StreamReaderProtocol._replace_writer = _replace_writer
StreamWriter.start_tls = start_tls
