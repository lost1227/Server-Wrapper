import json

servers = list()
current = dict()

def loadservers():
    global servers
    try:
        with open("servers.json",'r') as f:
            servers = json.loads(f.read())

        if type(servers) is list:
            for server in servers:
                if "name" in server and "default" in server and "data" in server:
                    if type(server["name"]) is str and type(server["default"]) is bool and type(server["data"]) is dict:
                        serverdata = server["data"]
                        if "server_dir" in serverdata and "run" in serverdata and "args" in serverdata:
                            if type(serverdata["server_dir"]) is str and type(serverdata["run"]) is str and type(serverdata["args"]) is list:
                                for arg in serverdata["args"]:
                                    if type(arg) is not str:
                                        raise ValueError('Bad argument type')
                            else: raise ValueError('Bad data types')
                        else: raise ValueError('Missing data key')
                    else: raise ValueError('Bad types')
                else: raise ValueError('Missing key')
        else: raise ValueError('Bad list')


    except json.decoder.JSONDecodeError:
        print("Error! servers.json is malformed. Server config cannot be loaded. Please check for syntax errors")
        return False
    except ValueError:
        print("Error! servers.json is malformed. Server config cannot be loaded. Please check that the structure is correct")
        return False
    return True

def getdefserver():
    for s in servers:
        if s["default"]:
            return s

def addserver(name,default,server_dir,run,args):
    servers.append({
        "name": name,
        "default": default,
        "data": {
            "server_dir": server_dir,
            "run": run,
            "args": args
        }
    })

def setcurrent(name):
    global current
    for s in servers:
        if s["name"] == name:
            current = s

def removeserver(name):
    remove = list()
    for s in servers:
        if s["name"] == name:
            list.append(s)
    for s in remove:
        servers.remove(s)

def saveservers():
    with open("servers.json", 'w') as f:
        f.write(json.dumps(servers, indent=4))
