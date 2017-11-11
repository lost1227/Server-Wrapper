# Server-Wrapper

A website and webserver that runs executables, and allows remote control of said servers via a websocket-based website.
Uses tornado webserver

Features a login page
![Login Page](/screenshots/login.png?raw=true)

The main console:
![Main Console](/screenshots/main.png?raw=true)
The console is used to interact with the server. It features a drop down menu to choose a server. The interrupt button sends a SIGINT signal, and the kill button kills the server.

### Configuration

![Example Config](/screenshots/config.png "Example Config")

 - "port": (integer) Sets the port the webserver listens on
 - "startonload": (boolean) Starts the default server as soon as the webserver starts
 - "addusers": (boolean) Configures whether to enable the /adduser page. Should only be set to true when adding new users
 - "cookie_secret": (string) Secret used to sign cookies. Should be kept private. This value is automatically generated, and should not be modified by the user.
 - "ssl": (dict) A set of settings for enabling SSL. Not in use, as I have not debugged SSL support, and do not plan to in the future.

 ### Servers

 ![Example Server List](/screenshots/servers.png "Example Server List")

 An array of servers. Each member has the following keys:
  - "name": (string) The display name of the server. MUST BE UNIQUE
  - "default": (boolean) Defines if the server is the default server
  - "data": (dict) Defines the details required to run the server
    - "server_dir": (string) Defines the path the server runs in
    - "run": (string) The executable to be run
    - "args": (array of string) An array of the parameters to be passed to the executable
