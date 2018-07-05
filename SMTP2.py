import sys
import re


# Generates a mail_from_cmd
def gen_from(s):
    return "MAIL FROM:" + s[5:].rstrip('\n') + '\n'


# Generates a rcpt_to_cmd
def gen_to(s):
    return "RCPT TO:" + s[3:].rstrip('\n') + '\n'


# Determines if a response is a success or not
def is_success(code, expected):

    filtered_code = int(re.search(r'\d+', code).group())
    return filtered_code == expected


# Prints output from a line and returns a state
def process_line(state, line):
    if state == "from":

        # Outputs mail-from-cmd
        sys.stdout.write(gen_from(line))

        # Reads response code
        message = sys.stdin.readline()

        # Echos response code
        sys.stderr.write(message)

        # If response if a success, we continue
        if is_success(message, 250):
            return "to"

        # If the response is not a success, we break and QUIT
        else:
            sys.stdout.write("QUIT\n")
            return "broken"

    elif state == "to":

        # Outputs rcpt-to-cmd
        sys.stdout.write(gen_to(line))

        # Reads response code
        message = sys.stdin.readline()

        # Echos response code
        sys.stderr.write(message)

        # If response if a success, we continue
        if is_success(message, 250):

            # Sends the DATA cmd
            sys.stdout.write("DATA\n")

            # Reads response code
            message = sys.stdin.readline()

            # Echos response code
            sys.stderr.write(message)

            # If response if a success, we continue
            if is_success(message, 354):
                return "data"

            # If the response is not a success, we break and QUIT
            else:
                sys.stdout.write("QUIT\n")
                return "broken"

        # If the response is not a success, we break and QUIT
        else:
            sys.stdout.write("QUIT\n")
            return "broken"

    elif state == "data":
        if line[0:5] == "From:":

            # Prints a . with newline to signify end of message
            sys.stdout.write(".\n")

            # Reads response code
            message = sys.stdin.readline()

            # Echos response code
            sys.stderr.write(message)

            # If response if a success, we continue
            if is_success(message, 250):
                return "from"

            # If the response is not a success, we break and QUIT
            else:
                sys.stdout.write("QUIT\n")
                return "broken"
        else:
            sys.stdout.write(line)
            return "data"


def read_input(path):
    # States for the state machine include: "from", "to", "data", or "break"
    state = "from"

    f = open(path, 'r')

    for line in f:
        while True:
            state = process_line(state, line)
            if state != "from":
                break
        if state == "broken":
            break

    # If we've reached the end of file in the data state, try to feed a \n.\n
    if state == "data":
        sys.stdout.write(".\n")

        # Reads response code
        message = sys.stdin.readline()

        # Echos response code
        sys.stderr.write(message)

    # Regardless of whether or not the end of message file was successful, we'll print "QUIT"
    sys.stdout.write("QUIT\n")


#sys.argv[1]
read_input(sys.argv[1])
