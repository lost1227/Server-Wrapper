import tornado.websocket
import tornado.web
import tornado.ioloop
import subprocess
import locale
from threading import Thread
import json
import os.path

connections = set()
def sendmessage(message):
    removable = set()
    for ws in connections:
        if not ws.ws_connection or not ws.ws_connection.stream.socket:
            removable.add(ws)
        else:
            ws.write_message(message)
    for ws in removable:
        connections.remove(ws)

def encodemessage(message):
    sendmessage(json.dumps(message));

def sendconsole(message):
    encodemessage({
        "type":"console",
        "content":{
            "output": message
        }
    })

class MainWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        self.set_nodelay(True)
        connections.add(self)

    def on_message(self, message):
        #print("Recieved message %s" % message)
        data = json.loads(message)
        try:
            if data["type"] == "console":
                writetoserver(data["data"],self)
            elif data["type"] == "start":
                global proc
                if type(data["data"]) is dict:
                    serverdata = data["data"]
                    if proc.poll() is not None:
                        if type(serverdata["server_dir"]) is str and type(serverdata["run"]) is str and type(serverdata["args"]) is list:
                            startserver(server_dir=serverdata["server_dir"],run=serverdata["run"],args=serverdata["args"])
                        else: raise ValueError("Bad JSON")
                else: raise ValueError("Bad JSON")
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

    def on_close(self):
        pass

class MainWebsite(tornado.web.RequestHandler):
    def get(self):
        self.render("dynamic/index.html")

class RenderPage(tornado.web.RequestHandler):
    def get(self):
        if(self.request.uri.endswith(".css")):
             self.set_header("Content-Type", 'text/css; charset="utf-8"')
        self.render(self.request.uri.strip("/"))

thread = None
proc = None
def startserver(server_dir=None,run="server.jar",args=["-Xmx1024M","-Xms1024M","nogui"]):
    process = ["java", "-jar", run]
    process.extend(args)
    #print("Starting process")
    global proc
    global thread
    proc = subprocess.Popen(process,stdin=subprocess.PIPE,stdout=subprocess.PIPE,encoding=locale.getpreferredencoding(),cwd=server_dir)
    #print("starting loop")
    thread = Thread(target=loopserver,kwargs={"proc":proc})
    thread.start()

def loopserver(proc):
    #print("Started loop")
    while proc.poll() == None:
        #print("reading line")
        line = proc.stdout.readline()
        if line != '':
            #print("sending line %s" % line)
            sendconsole(line.rstrip())
    #print("Loop terminated")

def writetoserver(inpt, sender=None):
    global proc
    if proc.poll() is None:
        proc.stdin.write(inpt + "\n")
        proc.stdin.flush()
    elif sender is not Null:
        sender.write_message(json.dumps({
            "type":"error",
            "content":{
                "output": "Server not running. %s cannot be run" % inpt
            }
        }))
    else:
        print("Can't execute %s, server not running",inpt)

if __name__ == '__main__':

    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static")
    }
    app = tornado.web.Application([
        (r"/",MainWebsite),
        (r"/dynamic/.*", RenderPage),
        (r"/ws", MainWebSocket),
    ],**settings)

    app.listen(8080)
    startserver(server_dir="C:\\Users\\jordan\\Desktop\\minecraft server",run="minecraft_server.1.12.1.jar")
    tornado.ioloop.IOLoop.current().start()
