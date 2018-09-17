from termcolor import colored


def print_good(msg):
    return f"{colored('[+]', 'green')} {msg}"


def print_bad(msg):
    return f"{colored('[-]', 'red')} {msg}"


def print_info(msg):
    return f"{colored('[*]', 'blue')} {msg}"
