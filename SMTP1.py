import sys
import re


#Different phases
class Phases: MAIL_FROM, RCPT_TO_FIRST, RCPT_TO, DATA, EOF = range(5)

#Possible Error Messages
error503 = "503 Bad sequence of commands"
error501 = "501 Syntax error in parameters or arguments"
error500 = "500 Syntax error: command unrecognized"


#resets the phases and writes to file
class SMTPState:
    def __init__(self):
        self.start()
    def start(self):
        self.state = Phases.MAIL_FROM
        self.from_mailbox = ""
        self.senders = []
        self.data = []
#creates/modifies a string to write to file and then uses the last loop to write the string to the file
    def writeToFile(self):
        if self.state != Phases.DATA:
            raise OutOfOrderException()
        str = "From: <" + self.from_mailbox + ">\n"
        for sender in self.senders:
                str += "To: <" + sender + ">\n"
        str += str.join("\n", self.data) + "\n"
        for sender in self.senders:
            with open("forward/" + sender, "a") as next:
                next.write(str)


# exception handling
class ParseException(Exception): pass


class OutOfOrderException(Exception): pass

# creates an smtp object
smtp = SMTPState()


# makes sure it is in the data state and then parses
def p_data(line):
    if smtp.state != Phases.DATA: raise OutOfOrderException()

    if line == ".":
        smtp.writeToFile()
        smtp.start()
        print("250 OK")
    else:
        smtp.data.append(line)

# checks the phase then uses check function to check if it is correct
#and edit it to the next part. Gives command to find data
def data(line):
    if smtp.state != Phases.RCPT_TO: raise OutOfOrderException()
    line = check("^DATA", "data-cmd", line)
    line = check("^[ \t]*[\r]?$", "data-cmd", line)
    smtp.state = Phases.DATA
    print("354 Start mail input; end with <CRLF>.<CRLF>")
# Same as above, prints 250 ok if matches are made
def rcpt(line):
    if smtp.state != Phases.RCPT_TO_FIRST and smtp.state != Phases.RCPT_TO:
        raise OutOfOrderException()
    line = check("^RCPT[ \t]+TO:[ \t]*", "rcpt-to-cmd", line)
    line, mailbox = match_path(line)
    line = check("^[ \t]*[\r]?$", "rcpt-to-cmd", line)
    smtp.senders.append(mailbox)
    smtp.state = Phases.RCPT_TO
    print("250 OK")


def mailfrom(line):
    if smtp.state != Phases.MAIL_FROM: raise OutOfOrderException()
    line = check("^MAIL[ \t]+FROM:[ \t]*", "mail-from-cmd", line)
    line, mailbox = match_path(line)
    line = check("^[ \t]*[\r]?$", "mail-from-cmd", line)

    smtp.from_mailbox = mailbox
    smtp.state = Phases.RCPT_TO_FIRST
    print("250 OK")

#looks for correct data pattern and then removes it. Allows to parse down the different evels
# and throw correct errors at the correct location
def check(pattern, name, token):
    bool = re.match(pattern, token)
    if  bool == None:
        raise ParseException(name)
    else:
        return re.sub(pattern, "", token)


#breaks down the path, if correct moves onto the next part. If failed throws error.
#If one part breaks into multiple parts the string is split by using groups
#returns token with path stripped
def match_path(s):
    match = re.match("^<(.+?)>", s)
    if match == None:
        raise ParseException("path")
    mailbox = match.group(1)
    match = re.match("^(.+?)@(.+?)$", match.group(1))
    if match == None:
        raise ParseException("mailbox")
    domain_elems = match.group(2).split(".")
    match = re.match(r"^[\x00-\x7F]+$", match.group(1))
    if match == None:
        raise ParseException("local-part")
    match = re.match(r"^[^ \t<>()\[\]\\\.,;:@\"]+$", match.group(0))
    if match == None:
        raise ParseException("local-part")
    for ele in domain_elems:
        match = re.match("^[a-zA-Z][a-zA-Z0-9]+$", ele)
        if match == None:
            raise ParseException("domain")
    return re.sub("^<(.+?)>", "", s), mailbox

#input
while smtp.states != Phases.EOF:
    try:
        input = raw_input()
        print(input)
        if smtp.state == Phases.DATA:
            p_data(input)
        elif re.match("^DATA", input):
            data(input)
        elif re.match("^RCPT[ \t]+TO:[ \t]*", input):
            rcpt(input)
        elif re.match("^MAIL[ \t]+FROM:[ \t]*", input):
            mailfrom(input)
        else:
            print(error500)
    except EOFError:
        smtp.state = Phases.EOF
    except ParseException as x:
        print(error501)
    except OutOfOrderException:
        print(error503)
        smtp.start()
