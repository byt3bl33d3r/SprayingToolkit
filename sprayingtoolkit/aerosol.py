#!/usr/bin/env python3

import lxml.html
import asyncio
import json
import boto3
import signal
import os
from sprayingtoolkit.core.utils.messages import print_info, print_good
from mitmproxy import http, ctx
#from IPython import embed


class Aerosol:
    def __init__(self):
        self.words = set()
        self.comprehend = None

        self.loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            self.loop.add_signal_handler(sig, self.shutdown)

    def load(self, loader):
        loader.add_option(
            name="target",
            typespec=str,
            default='',
            help="Target domain or URL"
        )

        loader.add_option(
            name="language",
            typespec=str,
            default='en',
            help='text language'
        )

        loader.add_option(
            name='aws_region',
            typespec=str,
            default='us-east-1',
            help='AWS region'
        )

    def running(self):
        if not self.comprehend:
            self.comprehend = boto3.client(
                service_name='comprehend',
                region_name=ctx.options.aws_region,
                aws_access_key_id=os.environ['AWS_ACCESS_KEY'],
                aws_secret_access_key=os.environ['AWS_SECRET_KEY']
            )

    def response(self, flow: http.HTTPFlow) -> None:
        try:
            if "html" in flow.response.headers["Content-Type"] and len(flow.response.content):
                if ctx.options.target in flow.request.host:
                    html = lxml.html.fromstring(flow.response.content)
                    the_best_words = set(html.xpath('//text()'))
                    ctx.log.info(print_good(f"Got {len(the_best_words)} words, the best words..."))
                    self.words |= the_best_words
        except KeyError:
            pass

    def shutdown(self):
        if len(self.words):
            text = ' '.join(self.words)

            ctx.log.info(print_info('Calling DetectKeyPhrases'))
            ctx.log.info(json.dumps(self.comprehend.detect_key_phrases(Text=text, LanguageCode=ctx.options.language), sort_keys=True, indent=4))

            ctx.log.info(print_info('Calling DetectEntities'))
            ctx.log.info(json.dumps(self.comprehend.detect_entities(Text=text, LanguageCode=ctx.options.language), sort_keys=True, indent=4))

        self.loop.stop()
        pending = asyncio.Task.all_tasks()
        self.loop.run_until_complete(asyncio.gather(*pending))


addons = [
    Aerosol()
]
