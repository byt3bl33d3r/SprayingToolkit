try: 
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

from core.parsers.linkedin import linkedin_se_name_parser


def google(content):
    names = []
    html = BeautifulSoup(content)

    for text in [e.text for e in html.body.findAll('h3', attrs={'class':'LC20lb'})]:
        first, last = linkedin_se_name_parser(text)
        if first or last:
            names.append((first, last, text))

    return names
