import tornado.web
import sqlite3
from passlib.hash import pbkdf2_sha256 as pcrypt
import uuid
import os

conn = None
c = None

loggedinusers = set()

def verifyTable():
    try:
        c.execute("SELECT name FROM sqlite_master WHERE type='table' and name='users';")
        if c.fetchall() == []:
            raise sqlite3.OperationalError("Table Missing")
        c.execute("PRAGMA table_info(users);")
        if c.fetchall() != [(0, 'key', 'INTEGER', 0, None, 1), (1, 'name', 'TEXT', 0, None, 0), (2, 'password', 'TEXT', 0, None, 0)]:
            c.execute("DROP TABLE users;")
            raise sqlite3.OperationalError("Malformed Table")
    except sqlite3.OperationalError:
        print("Password database malformed. Resetting...");
        init()

def execute(query, args=None):
    global c
    verifyTable()
    if args is None:
        c.execute(query)
    else:
        c.execute(query, args)

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
    execute("SELECT password FROM users WHERE name LIKE ?;",(name,))
    if c.fetchall() == []:
        execute("INSERT INTO users (name,password) VALUES (?,?);",(name,passhash))
        conn.commit()
        return('User created successfully. <a href="/">Login</a>')
    else:
        return("Cannot create user, user exists")

def deluser(name,passwd):
    if conn == None or c == None:
        init()
    if(testuser(name,passwd)):
        execute("DELETE FROM users WHERE name LIKE ?;",(name,))
        return('User deleted')
    else:
        return('Bad username/password')

def testuser(name,passwd):
    if conn == None or c == None:
        init()
    execute("SELECT password FROM users WHERE name LIKE ?;",(name,))
    res = c.fetchall()
    if res == []:
        return False
    else:
        return pcrypt.verify(passwd,res[0][0])

def changepass(name,passwd,newpasswd):
    if conn == None or c == None:
        init()
    if testuser(name,passwd):
        execute("UPDATE users SET password = ? WHERE name LIKE ?;",(newpasswd, name))
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
                self.write(adduser(self.get_body_argument("name"),self.get_body_argument("pass")))
            elif self.get_body_argument("method") == "remove":
                self.write(deluser(self.get_body_argument("name"),self.get_body_argument("pass")))
            else:
                changepass(self.get_body_argument("name"),self.get_body_argument("pass"),self.get_body_argument("newpass"))
        except tornado.web.MissingArgumentError:
            print("Missing argument")
