import socket
import time

import am2320
import machine
from config import NETWORK_PASSWORD, NETWORK_SSID

I2C = machine.I2C(scl=machine.Pin(14), sda=machine.Pin(2))
SENSOR = am2320.AM2320(I2C)


def do_connect():
    import network

    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("connecting to network...")
        sta_if.active(True)
        sta_if.connect(NETWORK_SSID, NETWORK_PASSWORD)
        while not sta_if.isconnected():
            pass
    print("network config:", sta_if.ifconfig())

    return sta_if


def get_data():
    SENSOR.measure()
    return "temperature {}\nhumidity {}".format(SENSOR.temperature(), SENSOR.humidity())


# connect to wifi
do_connect()

# webserver
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)

while True:
    cl, addr = s.accept()
    print("client connected from", addr)
    cl_file = cl.makefile("rwb", 0)

    while True:
        line = cl_file.readline()
        if not line or line == b"\r\n":
            break

    # try to get temp data
    status_code = "200"
    response = None
    resp_counter = 0
    while not response and resp_counter <= 5:
        try:
            response = get_data()
            print(response)
        except BaseException as e:
            print("got error trying to fetch data: {}".format(e))
            resp_counter += 1
            print("resp_counter: {}".format(resp_counter))
    if not response:
        response = ""
        status_code = "500"

    # create headers
    response_headers = {
        "Content-Type": "text/html; encoding=utf8",
        "Content-Length": len(response),
        "Connection": "close",
    }

    response_headers_raw = "".join(
        "%s: %s\n" % (k, v) for k, v in response_headers.items()
    )

    response_proto = "HTTP/1.1"
    response_status = status_code
    response_status_text = "FOO"  # this can be random

    cl.send("%s %s %s" % (response_proto, response_status, response_status_text))
    cl.send(response_headers_raw)
    cl.send("\n")
    cl.send(response)

    cl.close()
