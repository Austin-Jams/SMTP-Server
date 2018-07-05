import sys
import re
import socket


# Possible states of the state machine
class Phases:
    HELLO, FROM, TO, REV, DATA, EOF = range(6)


# Class to manage state of the machine
class Server_State:
    #initializes the connection and uses the reset method defined below to reset/initialize the state
    def __init__(self):
        self._conn = None
        self.reset()
#resets the state
    def reset(self):
        self.state = Phases.HELLO
        self.from_mailbox = ""
        self.to_mailboxes = []
        self.data = []

    def writeToFile(self):
        if self.state != Phases.DATA:
            raise OutOfOrderException()

        # Takes the address coming and inserts it into the format of the string we need to generate
        str = "From: <" + self.from_mailbox + ">\n"
        #Needs a loop because there could be multiple people that we want to sent to
        #takes the address and inserts it into the format we want
        for to_mailbox in self.to_mailboxes:
            str += "To: <" + to_mailbox + ">\n"
        #adds the data portion with a new line between lines and at the end
        str += str.join("\n", self.data) + "\n"

        #writing to the file
        for to_mailbox in self.to_mailboxes:
            domain = p_mb(to_mailbox)
            if domain in set():
                continue
            else:
                set().add(domain)

            with open(domain, "a") as s:
                s.write(str)
#checks if connection is established then sends all
    def send(self, toSend):
        if self._conn == None:
            print "Tried to send without connection"
        self._conn.sendall(toSend)


# Parse exceptions
class ParseException(Exception): 
    pass
class OutOfOrderException(Exception): 
    pass

#creates server state object
server = Server_State()


# Parse data while in state = DATA
def p_data(line):
    #raise exception if this is called without being in a state to receive data
    if server.state != Phases.DATA: 
        raise OutOfOrderException()

    if line == ".":
        server.writeToFile()
        #sends code
        server.send("250 OK")
        #resets states to possibly repeat
        server.reset()
    else:
        server.data.append(line)



def rec(line):
    if server.state != Phases.REV: 
        raise OutOfOrderException()
##checks for matches 
    #remember to hard code in the regex from style suggestions
    line = match("data-cmd", "^DATA", line)
    line = match("data-cmd", "^[ \t]*[\r]?$", line)
#sends 354
    server.state = Phases.DATA
    server.send("354 Start mail input; end with <CRLF>.<CRLF>")



def to(line):
    if server.state != Phases.TO and server.state != Phases.REV:
        raise OutOfOrderException()

    line = match("rcpt-to-cmd", "^RCPT[ \t]+TO:[ \t]*", line)
    line, mailbox = match_path(line)
    line = match("rcpt-to-cmd", "^[ \t]*[\r]?$", line)

    # Has gotten at least first RCPT_TO
    server.to_mailboxes.append(mailbox)
    server.state = Phases.REV
    server.send("250 OK")


def p_from(line):
    #as always check for state
    if server.state != Phases.FROM:
        raise OutOfOrderException()
#same thing as above just checking for matches with appropriate syntax through regex
    line = match("mail-from-cmd", "^MAIL[ \t]+FROM:[ \t]*", line)
    line, mailbox = match_path(line)
    line = match("mail-from-cmd", "^[ \t]*[\r]?$", line)
#sets to appropriate new state
    server.from_mailbox = mailbox
    server.state = Phases.TO
    server.send("250 OK")

#same as other match methods
#makes sure the state is correct
#makes sure it matches syntax
def helo(line):
    if server.state != Phases.HELLO:
        raise OutOfOrderException()
    line = match("helo", "^HELO", line)
    server.state = Phases.FROM
    #generates string to send
    server.send("250 " + line.strip() + ", pleased to meet you")


# checks patterns taking in the name of the syntax being checked, te syntax itself, and the string to be checked
def match(name, pattern, token):
    match = re.match(pattern, token)
    if match == None:
        raise ParseException(name)
    else:
        return re.sub(pattern, "", token)


def match_path(s):
    match = re.match("^<(.+?)>", s)
    if match == None:
        raise ParseException("path")
    p_mb(match.group(1))
    return re.sub("^<(.+?)>", "", s), match.group(1)


# Parse a mailbox. If found returns the domain of the mailbox, otherwise throw exception
def p_mb(mailbox):
    match = re.match("^<(.+?)@(.+?)$", mailbox)
    if match == None:
        raise ParseException("mailbox")

    domain = match.group(2)
    ele = domain.split(".")

    # simple check to make sure the elements are in ASCII
    match = re.match(r"^[\x00-\x7F]+$", match.group(1))
    if match == None:
        raise ParseException("local-part")
    match = re.match(r"^[^ \t<>()\[\]\\\.,;:@\"]+$", match.group(0))
    if match == None:
        raise ParseException("local-part")

    # Check all domain elements
    for s in ele:
        match = re.match("^[a-zA-Z][a-zA-Z0-9]+$", s)
        if match == None: raise ParseException("domain")

    return domain


# Main loop
def main():
    #if there are no arguments this indicates there are no ports
    try:
        if len(sys.argv) < 1:
            print "No port provided"
            return None
        #if there are arguments then we make it an integer and assign it as our port number
        else:
            portNumber = int(sys.argv[1])
    except:
        print "Invalid port provided " + sys.argv[1]
        return None

    ear = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Try starting the server
    try:
        #puts in proper syntax
        ear.bind(('',portNumber))
        #listens for connections to make to the socket
        ear.listen(1)
    except:
        print "Fail"
        return None

    while True:
        server._conn, _ = ear.accept()
        runSMTP()


# Run SMTP protocol for connection
def runSMTP():
    if server._conn == None:
        print "No connection"
        return None
#send code plus hostname
    #greeting message
    server.send("220 " + socket.gethostname())
    while True:
        try:
            response = server._conn.recv(1024).decode()
            if len(response) == 0:
                break
#break into new lines
            #sends it through each phase
            for line in response.split("\r\n"):
                # print(line)
                if server.state == Phases.DATA:
                    p_data(line)
                elif re.match("^HELO", line):
                    helo(line)
                elif re.match("^DATA", line):
                    rec(line)
                elif re.match("^RCPT[ \t]+TO:[ \t]*", line):
                    to(line)
                elif re.match("^MAIL[ \t]+FROM:[ \t]*", line):
                    p_from(line)
                elif line == "QUIT":
                    break
                else:
                    server.send("500 Syntax error: command unrecognized")

        except ParseException as e:
            server.send("501 Syntax error in parameters or arguments")
        except OutOfOrderException:
            server.send("503 Bad sequence of commands")
            break
            #resets
    server.reset()
    server._conn.close()
    server._conn = None


# Start
main()