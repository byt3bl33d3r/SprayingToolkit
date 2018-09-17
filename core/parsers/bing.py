import logging
import lxml.html
from termcolor import colored


def bing(content):
    names = set()
    html = lxml.html.fromstring(content)

    for result in html.xpath('//li[@class="b_algo"]/h2/a'):
        person = ''.join(result.xpath('.//text()'))
        logging.info(colored(person, 'yellow'))

        try:
            name, _ = person.split('-', 1)
        except ValueError:
            name, _ = person.split('|', 1)

        parts = name.split()
        try:
            first, last = parts
        except ValueError:
            # Cause people have middle names as well :(
            if len(parts) == 3:
                first, _, last = parts

        names.add((first, last))

    return names
