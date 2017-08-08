import subprocess
import locale
from threading import Thread
import json

class mserver:
    thread = None # The thread directing the output from the minecraft server to the client through the websockets
    proc = None # The process running the minecraft server
    web = None

    serverdetails = {
        "server_dir":None,
        "run":"server.jar",
        "args":["-Xmx1024M","-Xms1024M","nogui"]
    }

    def __init__(self,socket,server_dir=None,run="server.jar",args=["-Xmx1024M","-Xms1024M","nogui"]):
        self.web = socket
        self.serverdetails = {
            "server_dir":server_dir,
            "run":run,
            "args":args
        }

    def startserver(self):
        if self.serverdetails["run"].endswith(".jar"):
            process = ["java", "-jar", self.serverdetails["run"]]
        elif self.serverdetails["run"].endswith(".sh"):
            process = ["bash",self.serverdetails["run"]]
        else:
            process = [self.serverdetails["run"]]
        process.extend(self.serverdetails["args"])
        try:
            self.proc = subprocess.Popen(process,stdin=subprocess.PIPE,stdout=subprocess.PIPE,encoding=locale.getpreferredencoding(),cwd=self.serverdetails["server_dir"])
        except (NotADirectoryError, FileNotFoundError):
            print("Bad arguments")
            return
        thread = Thread(target=self.loopserver,kwargs={"proc":self.proc})
        thread.start()
        self.web.sendstatus(self)

    # The code running in the thread to direct the output form the minecraft server to the client through the websocket
    def loopserver(self,proc):
        while proc.poll() == None:
            line = proc.stdout.readline()
            if line != '':
                self.web.sendconsole(line.rstrip())
        self.web.sendstatus(self)

    # Send commands to the minecraft server
    def writetoserver(self,inpt, sender=None):
        global proc
        if self.proc is not None and self.proc.poll() is None:
            self.proc.stdin.write(inpt + "\n")
            self.proc.stdin.flush()
        elif sender is not None:
            sender.write_message(json.dumps({
                "type":"error",
                "content":{
                    "output": "Server not running. %s cannot be run" % inpt
                }
            }))
        else:
            print("Can't execute %s, server not running",inpt)

    def running(self):
        if self.proc is None:
            return False
        else:
            return self.proc.poll() is None

    def stopserver(self):
        if self.running():
            print("Waiting for minecraft to stop")
            self.writetoserver("stop")
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("Process failed to stop. Killing")
                self.proc.kill()
                self.proc.wait()
            print("Minecraft has been stopped")
