import json

import base64
import os

settings = dict()
loaded = bool()

def loadsettings():
    global settings
    global loaded
    try:
        with open("settings.json",'r') as f:
            settings = json.loads(f.read())
        if "port" in settings and "startonload" in settings and "addusers" in settings:
            if type(settings["port"]) is int and type(settings["startonload"]) is bool and type(settings["addusers"]) is bool:
                pass
            else: raise ValueError('Bad type')
        else: raise ValueError('Missing Field')
        if "cookie_secret" in settings:
            if type(settings["cookie_secret"]) is str:
                pass
        else:
            settings["cookie_secret"] = base64.b64encode(os.urandom(50)).decode('ascii')
            savesettings()
    except json.decoder.JSONDecodeError:
        print("Error! settings.json is malformed. Server config cannot be loaded. Please check for syntax errors")
        loaded = False
        return False
    except ValueError:
        print("Error! settings.json is malformed. Server config cannot be loaded. Please check that the structure is correct")
        loaded = False
        return False
    loaded = True
    return True

def savesettings():
    with open("settings.json", 'w') as f:
        f.write(json.dumps(settings, indent=4))
