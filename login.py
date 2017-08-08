import tornado.web
import sqlite3
from passlib.hash import pbkdf2_sha256 as pcrypt
import uuid

conn = None
c = None

loggedinusers = set()

def init():
    global conn
    global c
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' and name='users';")
    if c.fetchall() == []:
        c.execute("CREATE TABLE users(key INTEGER PRIMARY KEY, name TEXT, password TEXT);")
        conn.commit()

def adduser(name,passwd):
    if conn == None or c == None:
        init()
    passhash = pcrypt.hash(passwd)
    c.execute("SELECT password FROM users WHERE name LIKE ?;",(name,))
    if c.fetchall() == []:
        c.execute("INSERT INTO users (name,password) VALUES (?,?);",(name,passhash))
        conn.commit()
    else:
        print("Cannot create user, user exists")

def testuser(name,passwd):
    if conn == None or c == None:
        init()
    c.execute("SELECT password FROM users WHERE name LIKE ?;",(name,))
    res = c.fetchall()
    if res == []:
        return False
    else:
        return pcrypt.verify(passwd,res[0][0])

def changepass(name,passwd,newpasswd):
    if conn == None or c == None:
        init()
    if testuser(name,passwd):
        c.execute("UPDATE users SET password = ? WHERE name LIKE ?;",(newpasswd, name))
        conn.commit()

def isloggedin(uid):
    if uid == None:
        return False
    uid = uid.decode('ascii')
    if conn == None or c == None:
        init()
    #print("Testing if %s is in" % uid, loggedinusers)
    #print("Got ", uid in loggedinusers)
    return uid in loggedinusers

class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("protected/login.html")
    def post(self):
        global loggedinusers
        try:
            if testuser(self.get_body_argument("name"),self.get_body_argument("pass")):
                userid = str(uuid.uuid4())
                self.set_secure_cookie("auth",userid)
                loggedinusers.add(userid)
                self.redirect(r"/")
            else:
                self.render("protected/login.html")
        except tornado.web.MissingArgumentError:
            print("Missing argument")
class AddUser(tornado.web.RequestHandler):
    def get(self):
        self.render("protected/adduser.html")
    def post(self):
        try:
            if self.get_body_argument("method") == "add":
                adduser(self.get_body_argument("name"),self.get_body_argument("pass"))
            else:
                changepass(self.get_body_argument("name"),self.get_body_argument("pass"),self.get_body_argument("newpass"))
        except tornado.web.MissingArgumentError:
            print("Missing argument")
