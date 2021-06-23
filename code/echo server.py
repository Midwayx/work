import asyncio


async def handle_tcp_echo(reader, writer):
    print("Connection from {}".format(writer.get_extra_info("peername")))
    while True:
        data = await reader.read(100)
        if data:
            message = data.decode()
            print("Echoing back: {!r}".format(message))
            writer.write(data)
            await writer.drain()
        else:
            print("Terminating connection")
            writer.close()
            break


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        asyncio.ensure_future(
            asyncio.start_server(handle_tcp_echo, "127.0.0.1", 7777), loop=loop
        )
    )
    loop.run_forever()
