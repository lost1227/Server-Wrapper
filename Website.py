import tornado.websocket
import tornado.web
import tornado.ioloop
import subprocess
import locale
from threading import Thread
import json
import os.path
if __name__ == '__main__':
    import Minecraft as mserver

# The set of open websockets
connections = set()
# Polls all the websockets in the set and sends them a message
def sendmessage(message):
    removable = set()
    for ws in connections:
        if not ws.ws_connection or not ws.ws_connection.stream.socket:
            removable.add(ws)
        else:
            ws.write_message(message)
    for ws in removable:
        connections.remove(ws) # remove dead connections

def encodemessage(message):
    sendmessage(json.dumps(message));

def sendconsole(message):
    encodemessage({
        "type":"console",
        "content":{
            "output": message
        }
    })

# The main handler for websocket connections
class MainWebSocket(tornado.websocket.WebSocketHandler):
    # Adds the newly formed websocket to the set of websockets
    def open(self):
        self.set_nodelay(True)
        connections.add(self)

    # Recieves a message from the websocket. Decodes the JSON, then figures out how to handle the message
    def on_message(self, message):
        #print("Recieved message %s" % message)
        data = json.loads(message)
        try:
            if data["type"] == "console":
                mserver.writetoserver(data["data"],self)
            elif data["type"] == "start":
                if type(data["data"]) is dict:
                    serverdata = data["data"]
                    if not mserver.running():
                        if type(serverdata["server_dir"]) is str and type(serverdata["run"]) is str and type(serverdata["args"]) is list:
                            mserver.startserver(server_dir=serverdata["server_dir"],run=serverdata["run"],args=serverdata["args"])
                        else: raise ValueError("Bad JSON")
                else: raise ValueError("Bad JSON")
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
        self.render(self.request.uri.strip("/"))

# Stop the running webserver
def stopwebserver():
    mserver.stopserver()
    tornado.ioloop.IOLoop.instance().stop()

# Check for input telling the server to stop
def pollstop():
    while True:
        inp = input(">")
        if(inp == "exit"):
            stopwebserver()
            break

if __name__ == '__main__':
    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static")
    }
    app = tornado.web.Application([
        (r"/",MainWebsite),
        (r"/dynamic/.*", RenderPage),
        (r"/ws", MainWebSocket),
    ],**settings)

    stop = Thread(target=pollstop)
    stop.start()

    app.listen(8080)
    mserver.startserver(server_dir="C:\\Users\\jordan\\Desktop\\minecraft server",run="minecraft_server.1.12.1.jar")
    tornado.ioloop.IOLoop.current().start()
