import logging
import lxml.html
from termcolor import colored


def google(content):
    names = set()
    html = lxml.html.fromstring(content)

    for person in html.xpath('//h3[@class="r"]//text()'):
        logging.info(colored(person, 'yellow'))
        try:
            name, _ = person.split('-', 1)
        except ValueError:
            name, _ = person.split('|', 1)

        try:
            first, last = name.split()
        except ValueError:
            # This means there's some junk after the name and before the hyphen
            first, last = name.split()[:2]

        names.add((first, last))

    return names
