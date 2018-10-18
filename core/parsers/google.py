import lxml.html
from core.parsers.linkedin import linkedin_se_name_parser


def google(content):
    names = []
    html = lxml.html.fromstring(content)

    for text in html.xpath('//h3[@class="LC20lb"]//text()'):
        first, last = linkedin_se_name_parser(text)
        names.append((first, last, text))

    return names
