import tornado.websocket
import tornado.web
import tornado.ioloop
import subprocess
import locale
from threading import Thread
import json
import os.path
if __name__ == '__main__':
    import Minecraft

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
                if type(data["data"]) is dict:
                    serverdata = data["data"]
                    if not mserver.running():
                        if type(serverdata["server_dir"]) is str and type(serverdata["run"]) is str and type(serverdata["args"]) is list:
                            mserver = Minecraft.mserver(server_dir=serverdata["server_dir"],run=serverdata["run"],args=serverdata["args"])
                            mserver.startserver()
                        else: raise ValueError("Bad JSON")
                elif type(data["data"]) is str and data["data"] == "start":
                    if not mserver.running():
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
                    "output": "Improper directory. %s is not a valid path" % serverdata["server_dir"]
                }
            }))

    # Don't do anything when the websocket closes
    def on_close(self):
        pass
# Handler for index.html at the webroot
class MainWebsite(tornado.web.RequestHandler):
    def get(self):
        self.render("dynamic/index.html")

# Handler for all other dynamically generated pages in the /dynamic/ folder
class RenderPage(tornado.web.RequestHandler):
    def get(self):
        if(self.request.uri.endswith(".css")):
             self.set_header("Content-Type", 'text/css; charset="utf-8"')
        elif(self.request.uri.endswith(".js")):
            self.set_header("Content-Type", 'text/javascript; charset="utf-8"')
        self.render(self.request.uri.strip("/"))

# Stop the running webserver
def stopwebserver():
    global running
    running = False
    mserver.stopserver()
    tornado.ioloop.IOLoop.instance().stop()

# Check for input telling the server to stop
running = True
def pollstop():
    while running:
        inp = input(">")
        if(inp == "exit"):
            stopwebserver()
        elif(inp == "status"):
            print(mserver.proc.poll() is None);

if __name__ == '__main__':
    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static")
    }
    app = tornado.web.Application([
        (r"/",MainWebsite),
        (r"/dynamic/.*", RenderPage),
        (r"/ws", MainWebSocket),
    ],**settings)

    socks = Socketinterface()
    mserver = Minecraft.mserver(socket=socks,server_dir="C:\\Users\\jordan\\Desktop\\minecraft server",run="minecraft_server.1.12.1.jar")

    stop = Thread(target=pollstop)
    stop.start()

    app.listen(8080)
    mserver.startserver()
    #mserver.startserver(server_dir="/home/jordan/Downloads/minecraft_server",run="minecraft_server.1.12.1.jar")
    tornado.ioloop.IOLoop.current().start()
