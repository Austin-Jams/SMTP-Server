import sys
import re
from socket import *

#receives the code and returns it as a variable to be used in other functions
def receive_code():
    response = client.recv(1024).decode()
    return response


def s_body(from_addr, to_addr, sub, body):
    # Send data command
    client.sendall("DATA")
    #checks code
    if "^354".match(receive_code) == None:
        raise Exception("%s is an invalid code" % receive_code())
    # Sends all of the header
    client.sendall("From: " + from_addr)
    client.sendall("To: " + ",".join(to_addr) + "\r\n")
    client.sendall("Subject: " + sub + "\r\n")
    client.sendall("\r\n")
    for line in body: client.sendall(line + "\r\n")
    client.sendall(".")
    #checks code
    if "^250".match(receive_code()) == None:
        raise Exception("%s is an invalid code" % receive_code())


def p_from(from_addr):
    #creates proper syntax
    client.sendall("MAIL FROM: <" + from_addr + ">")
    #checks code
    if "^250".match(receive_code()) == None:
        raise Exception("%s is not 250" % receive_code())


def p_to(to_addr):
    for mailbox in to_addr:
        client.sendall("RCPT TO: <" + mailbox + ">")
        if "^250".match(receive_code()) == None: raise \
            Exception("Expected 250, got %s" % receive_code())

#checks codes
def p_helo(response):
    if "^220".match(response) == None:
        raise Exception("%s is not 220" % response)
    client.sendall("HELO cs.unc.edu")
    if "^250".match(receive_code()) == None:
        raise Exception("%s is not 250" % receive_code())


def mail_check(addr):
    #checks syntax
    match = re.match("^(.+?)@(.+?)$", addr)
    if match == None:
        return False
    domain = match.group(2)
    ele = domain.split(".")
    #broken up the domain elements and now is checking the subgroups and individual elements
    match = re.match(r"^[\x00-\x7F]+$", match.group(1))
    if match == None:
        return False
    match = re.match(r"^[^ \t<>()\[\]\\\.,;:@\"]+$", match.group(0))
    if match == None:
        return False

    # Check all domain elements
    for d in ele:
        match = re.match("^[a-zA-Z][a-zA-Z0-9]+$", d)
        if match == None:
            return False
    return True

#assigns the host, port number, and client
host = sys.argv[1]
port_number = int(sys.argv[2])
client = socket(AF_INET, SOCK_STREAM)


def main():
    # check from addr
    while True:
        #makes sure the format is correct or break
        f_addr = raw_input("From: ")
        if mail_check(f_addr):
            break
        else:
            print(f_addr + "is wrong")

    # Get check to addr and apply proper additions
    while True:
        to_addr = raw_input("To: ").split(",")
        invalid = False
        for addr in to_addr:
            if not mail_check(addr):
                print(addr + "is incorrect")
                invalid = True
        if not invalid: break

    sub = raw_input("Subject: ")

    # Reads through the body by creating an array
    print "Message:"
    body = []
    while True:
        s = raw_input()
        if s == ".": break
        body.append(s)

    # Connects to the server using the host/port number
    try:
        client.connect((host, port_number))
    except:
        print("Failure")
        return

    try:
        #goes through al the checks and waits for the resposne
        p_helo(receive_code())
        p_from(f_addr)
        p_to(to_addr)
        s_body(f_addr, to_addr, sub, body)
    except Exception as exception:
        print(exception)

    client.sendall("QUIT")
main()
client.close()