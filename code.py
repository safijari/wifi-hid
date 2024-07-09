import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.mouse import Mouse
from adafruit_hid.keycode import Keycode
import ipaddress
import json

import wifi
wifi_creds = json.load(open("wifi.json"))
wifi.radio.connect(wifi_creds["ssid"], wifi_creds["password"])

from asyncio import create_task, gather, run, sleep as async_sleep
import board
import microcontroller
import neopixel
import socketpool
import wifi

from adafruit_httpserver import Server, Request, Response, Websocket, GET

keyboard = Keyboard(usb_hid.devices)
mouse = Mouse(usb_hid.devices)
pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, debug=True)

pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)

websocket: Websocket = None

HTML_TEMPLATE = open("index.html").read()


@server.route("/client", GET)
def client(request: Request):
    return Response(request, HTML_TEMPLATE, content_type="text/html")


@server.route("/connect-websocket", GET)
def connect_client(request: Request):
    global websocket  # pylint: disable=global-statement

    if websocket is not None:
        websocket.close()  # Close any existing connection

    websocket = Websocket(request)

    return websocket


server.start(str(wifi.radio.ipv4_address))


async def handle_http_requests():
    while True:
        server.poll()
        await async_sleep(0)

async def run_ping():
    while True:
        print(wifi.radio.ping(ipaddress.IPv4Address("8.8.8.8")))
        print(wifi.radio.hostname, wifi.radio.ipv4_gateway, wifi.radio.ipv4_address)
        await async_sleep(1)

async def handle_websocket_requests():
    while True:
        if websocket is not None:
            if (data := websocket.receive(fail_silently=True)) is not None:
                val = json.loads(data)
                print(val)
                if val["type"] == "mousemove":
                    mouse.move(int(val["dx"]), int(val["dy"]))
                if val["type"] == "click":
                    mouse.click(Mouse.LEFT_BUTTON)
                if val["type"] == "rightclick":
                    mouse.click(Mouse.RIGHT_BUTTON)
                # print(data)
                # key = data[0]
                # keyboard.press(Keycode.A)  # Change this to the appropriate Keycode
                # keyboard.release_all()
                # mouse.move(50, 50)
        await async_sleep(0)


async def send_websocket_messages():
    while True:
        if websocket is not None:
            cpu_temp = round(microcontroller.cpu.temperature, 2)
            websocket.send_message(str(cpu_temp), fail_silently=True)

        await async_sleep(1)


async def main():
    await gather(
        create_task(run_ping()),
        create_task(handle_http_requests()),
        create_task(handle_websocket_requests()),
        create_task(send_websocket_messages()),
    )


run(main())

# while True:
#     try:
#         # Listen for incoming UDP messages
#         data, addr = udp_socket.recvfrom(1024)
        
#         # Assuming single characters are sent over UDP
#         if len(data) == 1:
#             # Convert the received data to uppercase and send as keyboard input
#             key = chr(data[0]).upper()
#             keyboard.press(Keycode.KEY_A)  # Change this to the appropriate Keycode
#             keyboard.release_all()

#     except Exception as e:
#         print("Error:", e)

#     time.sleep(0.1)  # Adjust the sleep duration as needed
