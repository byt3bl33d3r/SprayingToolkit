import lxml.html
from core.parsers.linkedin import linkedin_se_name_parser


def bing(content):
    names = []
    html = lxml.html.fromstring(content)

    for result in html.xpath('//li[@class="b_algo"]/h2/a'):
        text = ''.join(result.xpath('.//text()'))

        first, last = linkedin_se_name_parser(text)
        names.append((first, last, text))

    return names
