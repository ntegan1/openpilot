#!/usr/bin/env python3
import time
import threading
from flask import Flask
from struct import unpack

import sys
import ssl
sys.path.append('/data/openpilot/third_party/websockets/src')
KEYDIR = "/data/openpilot/tools/joystick/keys"
import asyncio
from websockets import serve
sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
sslctx.load_cert_chain(f"{KEYDIR}/server.cert.pem", f"{KEYDIR}/server.key.pem")
sslctx.check_hostname = False

import cereal.messaging as messaging

app = Flask(__name__)
pm = messaging.PubMaster(['testJoystick'])

index = """
<html>
<head>
<script src="https://github.com/bobboteck/JoyStick/releases/download/v1.1.6/joy.min.js"></script>
</head>
<body>
<div id="joyDiv" style="width:100%;height:100%"></div>
<script type="text/javascript">
// Set up gamepad handlers
let gamepad = null;
var ws = new WebSocket('wss://' + location.hostname + ':5001');
window.addEventListener("gamepadconnected", function(e) {
  gamepad = e.gamepad;
});
window.addEventListener("gamepaddisconnected", function(e) {
  gamepad = null;
});
// Create JoyStick object into the DIV 'joyDiv'
var joy = new JoyStick('joyDiv');
var axes = new Float32Array([0.0, 0.0]);
setInterval(function(){
  var x = -joy.GetX()/100;
  var y = joy.GetY()/100;
  if (x === 0 && y === 0 && gamepad !== null) {
    let gamepadstate = navigator.getGamepads()[gamepad.index];
    x = -gamepadstate.axes[0];
    y = -gamepadstate.axes[1];
  }
  axes[0] = x;
  axes[1] = y;
  ws.send(axes);
}, 50);
</script>
"""

@app.route("/")
def hello_world():
  return index

last_send_time = time.monotonic()
async def handle(ws):
  async for message in ws:
    global last_send_time
    if not len(message) == 8:
      pass
    else:
      x,y = unpack('ff', message)
      x = max(-1, min(1, x))
      y = max(-1, min(1, y))
      dat = messaging.new_message('testJoystick')
      dat.testJoystick.axes = [y,x]
      dat.testJoystick.buttons = [False]
      pm.send('testJoystick', dat)
      last_send_time = time.monotonic()

async def maine():
  async with serve(handle, "0.0.0.0", 5001, ssl=sslctx):
    await asyncio.Future() # run forever
def websocket_thread():
  asyncio.run(maine())

def handle_timeout():
  while 1:
    this_time = time.monotonic()
    if (last_send_time+0.5) < this_time:
      #print("timeout, no web in %.2f s" % (this_time-last_send_time))
      dat = messaging.new_message('testJoystick')
      dat.testJoystick.axes = [0,0]
      dat.testJoystick.buttons = [False]
      pm.send('testJoystick', dat)
    time.sleep(0.1)

def main():
  threading.Thread(target=handle_timeout, daemon=True).start()
  threading.Thread(target=websocket_thread, daemon=True).start()
  app.run(host="0.0.0.0", ssl_context=(f"{KEYDIR}/server.cert.pem", f"{KEYDIR}/server.key.pem"))

if __name__ == '__main__':
  main()
