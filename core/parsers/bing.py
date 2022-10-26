try: 
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

from core.parsers.linkedin import linkedin_se_name_parser


def bing(content):
    names = []
    html = BeautifulSoup(content)

    try:
        for result in html.body.findAll('li', attrs={'class':'b_algo'}):
            text = result.find('h2').find('a').text
            first, last = linkedin_se_name_parser(text)
            if first or last:
                names.append((first, last, text))

    except AttributeError:
        pass

    return names
