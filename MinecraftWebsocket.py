import tornado.websocket
import tornado.web
import tornado.ioloop
import subprocess
import locale
from threading import Thread
import json
import os.path

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

thread = None # The thread directing the output from the minecraft server to the client through the websockets
proc = None # The process running the minecraft server
def startserver(server_dir=None,run="server.jar",args=["-Xmx1024M","-Xms1024M","nogui"]):
    process = ["java", "-jar", run]
    process.extend(args)
    global proc
    global thread
    proc = subprocess.Popen(process,stdin=subprocess.PIPE,stdout=subprocess.PIPE,encoding=locale.getpreferredencoding(),cwd=server_dir)
    thread = Thread(target=loopserver,kwargs={"proc":proc})
    thread.start()

# The code running in the thread to direct the output form the minecraft server to the client through the websocket
def loopserver(proc):
    while proc.poll() == None:
        line = proc.stdout.readline()
        if line != '':
            sendconsole(line.rstrip())

# Send commands to the minecraft server
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

# Stop the running webserver
def stopwebserver():
    global proc
    if proc.poll() is None:
        writetoserver("stop")
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print("Process failed to stop. Killing")
            proc.kill()
            proc.wait()
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
    startserver(server_dir="C:\\Users\\jordan\\Desktop\\minecraft server",run="minecraft_server.1.12.1.jar")
    tornado.ioloop.IOLoop.current().start()
