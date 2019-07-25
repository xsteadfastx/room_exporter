import am2320
import machine
import network
from config import NETWORK_PASSWORD, NETWORK_SSID

try:
    import uasyncio as asyncio
except ImportError:
    import upip

    upip.install("uasyncio")
    import uasyncio as asyncio

I2C = machine.I2C(scl=machine.Pin(14), sda=machine.Pin(2))
SENSOR = am2320.AM2320(I2C)


async def get_data():
    try_counter = 0
    temp = None
    hum = None
    while try_counter <= 5 and not temp and not hum:
        try:
            SENSOR.measure()
            temp = SENSOR.temperature()
            hum = SENSOR.humidity()
        except BaseException as e:
            print("problem with sensor: {}".format(e))
            try_counter += 1
            print("try counter: {}".format(try_counter))
    return "temperature {}\nhumidity {}".format(temp, hum)


async def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("connecting to network...")
        sta_if.active(True)
        sta_if.connect(NETWORK_SSID, NETWORK_PASSWORD)
        while not sta_if.isconnected():
            pass
        print("network config:", sta_if.ifconfig())
    else:
        print("still connected")

    return sta_if


async def serve(reader, writer):
    print((await reader.read()))

    data = await get_data()
    print("got data: {}".format(data))

    # create headers
    response_headers = {
        "Content-Type": "text/html; encoding=utf8",
        "Content-Length": len(data),
        "Connection": "close",
    }

    response_headers_raw = "".join(
        "%s: %s\n" % (k, v) for k, v in response_headers.items()
    )

    response_proto = "HTTP/1.1"
    response_status = "200"
    response_status_text = "OK"

    # send data
    await writer.awrite(
        "%s %s %s" % (response_proto, response_status, response_status_text)
    )
    await writer.awrite(response_headers_raw)
    await writer.awrite("\n")
    await writer.awrite(data)
    # await writer.awrite("HTTP/1.0 200 OK\r\n\r\n{}\r\n".format(data))

    print("closing writer...")
    await writer.aclose()
    print("finished processing request")


async def connection_fixer():
    while True:
        await do_connect()
        await asyncio.sleep(10)


def run():
    loop = asyncio.get_event_loop()
    loop.call_soon(asyncio.start_server(serve, "0.0.0.0", 80))
    loop.create_task(connection_fixer())
    loop.run_forever()
    loop.close()


run()
