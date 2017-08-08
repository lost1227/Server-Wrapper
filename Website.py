import tornado.websocket
import tornado.web
import tornado.ioloop
import tornado.httpserver
import subprocess
import locale
from threading import Thread
import json
import os.path
import Minecraft
import ServerManager as sm
import Settings
import login

import sys

import signal
from functools import partial
import time


class Socketinterface:
    # The set of open websockets
    connections = set()
    # Polls all the websockets in the set and sends them a message
    def sendmessage(self,message):
        removable = set()
        for ws in self.connections:
            if not ws.ws_connection or not ws.ws_connection.stream.socket:
                removable.add(ws)
            else:
                ws.write_message(message)
        for ws in removable:
            self.connections.remove(ws) # remove dead connections

    def encodemessage(self,message):
        self.sendmessage(json.dumps(message));

    def sendconsole(self,message):
        self.encodemessage({
            "type":"console",
            "content":{
                "output": message
            }
        })

    def sendstatus(self,server):
        self.encodemessage({
            "type":"status",
            "content":{
                "active": server.running()
            }
        })

class RedirectToSSL(tornado.websocket.WebSocketHandler):
    def get(self):
        self.redirect("https://%s" % self.request.full_url()[len("http://"):], permanent=True)
# The main handler for websocket connections
class MainWebSocket(tornado.websocket.WebSocketHandler):
    # Adds the newly formed websocket to the set of websockets
    def open(self):
        self.set_nodelay(True)
        socks.connections.add(self)

    # Recieves a message from the websocket. Decodes the JSON, then figures out how to handle the message
    def on_message(self, message):
        global mserver
        #print("Recieved message %s" % message)
        try:
            data = json.loads(message)
            if data["type"] == "console":
                mserver.writetoserver(data["data"],self)
            elif data["type"] == "start":
                if type(data["data"]) is str:
                    if data["data"] == "start":
                        if not mserver.running():
                            mserver.startserver()
                    else:
                        if not mserver.running():
                            sm.setcurrent(data["data"])
                            mserver = Minecraft.mserver(socket=socks,server_dir=sm.current["data"]["server_dir"],run=sm.current["data"]["run"],args=sm.current["data"]["args"])
                            mserver.startserver()
                else: raise ValueError("Bad JSON")
            elif data["type"] == "status":
                socks.sendstatus(mserver)
            elif data["type"] == "stop_webserver":
                stopwebserver()
            else:
                raise ValueError("Bad JSON")
        except (ValueError,KeyError,json.decoder.JSONDecodeError):
            self.write_message(json.dumps({
                "type":"error",
                "content":{
                    "output": "Malformed JSON. %s cannot be understood by this server" % message
                }
            }))
        except NotADirectoryError:
            self.write_message(json.dumps({
                "type":"error",
                "content":{
                    "output": "Improper directory. %s is not a valid path" % sm.current["data"]["server_dir"]
                }
            }))

    # Don't do anything when the websocket closes
    def on_close(self):
        pass

# Handler for index.html at the webroot
class MainWebsite(tornado.web.RequestHandler):
    def get(self):
        if login.isloggedin(self.get_secure_cookie("auth")):
            self.render("protected/index.html", servers=sm.servers, current=sm.current["name"])
        else:
            self.write("Not logged in")
            self.redirect(r"/login")

# Handler for all other dynamically generated pages in the /dynamic/ folder
class RenderPage(tornado.web.RequestHandler):
    def get(self):
        if(self.request.uri.endswith(".css")):
             self.set_header("Content-Type", 'text/css; charset="utf-8"')
        elif(self.request.uri.endswith(".js")):
            self.set_header("Content-Type", 'text/javascript; charset="utf-8"')
        try:
            self.render(self.request.uri.strip("/"))
        except FileNotFoundError:
            self.send_error(404)

# Stop the running webserver
def stopwebserver():
    mserver.stopserver()
    tornado.ioloop.IOLoop.instance().stop()

MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 3
def sig_handler(server, sig, frame):
    io_loop = tornado.ioloop.IOLoop.instance()

    def stop_loop(deadline):
        now = time.time()
        if now < deadline and (io_loop._callbacks or io_loop._timeouts):
            print('Waiting for next tick')
            io_loop.add_timeout(now + 1, stop_loop, deadline)
        else:
            io_loop.stop()
            print('Shutdown finally')

    def shutdown():
        print('Stopping http server')
        server.stop()
        print('Will shutdown in %s seconds ...' % MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
        stop_loop(time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)

    print('Caught signal: %s' % sig)
    print('Stopping minecraft server')
    mserver.stopserver()
    io_loop.add_callback_from_signal(shutdown)

if __name__ == '__main__':
    Settings.loadsettings()
    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static"),
        "cookie_secret": Settings.settings["cookie_secret"]
    }
    if Settings.settings["addusers"]:
        app = tornado.web.Application([
            (r"/",MainWebsite),
            (r"/dynamic/.*", RenderPage),
            (r"/ws", MainWebSocket),
            (r"/login", login.LoginHandler),
            (r"/adduser", login.AddUser)
        ],**settings)
    else:
        app = tornado.web.Application([
            (r"/",MainWebsite),
            (r"/dynamic/.*", RenderPage),
            (r"/ws", MainWebSocket),
            (r"/login", login.LoginHandler)
        ],**settings)

    socks = Socketinterface()

    if not sm.loadservers():
        stopwebserver()
    sm.current = sm.getdefserver()

    mserver = Minecraft.mserver(socket=socks,server_dir=sm.current["data"]["server_dir"],run=sm.current["data"]["run"],args=sm.current["data"]["args"])

    if Settings.loaded and Settings.settings["ssl"]["enabled"]:
        server = tornado.httpserver.HTTPServer(app,ssl_options={
            "certfile":Settings.settings["ssl"]["certfile"],
            "keyfile":Settings.settings["ssl"]["keyfile"]
        })
        server.listen(Settings.settings["ssl"]["port"])

        redirapp = tornado.web.Application([
        (r"/.*", RedirectToSSL)
        ])
        redirapp.listen(Settings.settings["port"])
    else:
        server = app.listen(Settings.settings["port"])

    signal.signal(signal.SIGTERM, partial(sig_handler, server))
    signal.signal(signal.SIGINT, partial(sig_handler, server))

    if Settings.loaded and Settings.settings["startonload"]:
        mserver.startserver()
    #mserver.startserver(server_dir="/home/jordan/Downloads/minecraft_server",run="minecraft_server.1.12.1.jar")
    tornado.ioloop.IOLoop.current().start()
