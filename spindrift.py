#! /usr/bin/env python3

"""
Usage:
    spindrift [<file>] [--target TARGET | --domain DOMAIN] [--format FORMAT]

Arguments:
    file    file containing names, can also read from stdin

Options:
    --target TARGET   optional domain or url to retrieve the internal domain name from OWA
    --domain DOMAIN   manually specify the domain to append to each username
    --format FORMAT   username format [default: {f}{last}]
"""

import sys
from docopt import docopt
from core.sprayers.owa import OWA


def convert_to_ad_username(name, username_format, domain):
    first, last = name.strip().split()
    username = username_format.format(first=first, last=last, f=first[:1], l=last[:1])
    print(f"{domain.upper()}\\{username.lower()}" if domain else username.lower())


if __name__ == '__main__':

    args = docopt(__doc__)
    contents = open(args['<file>']) if args['<file>'] else sys.stdin

    domain = None

    if args['--target']:
        owa = OWA(args['--target'])
        domain = owa.netbios_domain

    elif args['--domain']:
        domain = args['--domain']

    for line in contents:
        convert_to_ad_username(line, args['--format'], domain)
