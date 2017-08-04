import subprocess
import locale
from threading import Thread
import json
import Website as web

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
            web.sendconsole(line.rstrip())

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

def running():
    global proc
    return proc.poll is None

def stopserver():
    global proc
    if running():
        writetoserver("stop")
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print("Process failed to stop. Killing")
            proc.kill()
            proc.wait()
