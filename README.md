# SprayingToolkit

<p align="center">
  <img src="http://38.media.tumblr.com/79d7e2a376cb96fb581b3453070f6229/tumblr_ns5suorqYu1szok8ro1_500.gif" alt="SprayingToolkit"/>
</p>


## Description

A set of Python scripts/utilities that *tries* to make password spraying attacks against Lync/S4B & OWA a lot quicker, less painful and more efficient.

### Brought To You By

<p align="center">
  <a href="https://www.blackhillsinfosec.com/">
    <img src="https://www.blackhillsinfosec.com/wp-content/uploads/2016/03/BHIS-logo-L-300x300.png" alt="blackhillsinfosec"/>
  </a>
</p>

## Tool Overview

### Atomizer

A blazing fast password sprayer for Lync/Skype For Business and OWA, built on Asyncio and Python 3.7

#### Usage
```
Usage:
    atomizer (lync|owa) <domain> <password> --userfile USERFILE [--threads THREADS] [--debug]
    atomizer (lync|owa) <domain> --recon [--debug]
    atomizer -h | --help
    atomizer -v | --version

Arguments:
    domain     target domain
    password   password to spray

Options:
    -h, --help               show this screen
    -v, --version            show version
    -u, --userfile USERFILE  file containing usernames (one per line)
    -t, --threads THREADS    number of concurrent threads to use [default: 3]
    -d, --debug              enable debug output
    --recon                  only collect info, don't password spray
```

### Vaporizer

A port of [@OrOneEqualsOne](https://twitter.com/OrOneEqualsOne)'s [GatherContacts](https://github.com/clr2of8/GatherContacts) Burp extension to [mitmproxy](https://mitmproxy.org/) with some improvements.

Scrapes Google and Bing for LinkedIn profiles, automatically generates emails from the profile names using the specified pattern and performes password sprays in real-time.

(Built on top of Atomizer)

#### Usage

```
mitmdump -s vaporizer.py --set sprayer=(lync|owa) --set domain=domain.com --set password=password --set email_format='{f}.{last}'
```

By default `email_format` is set to `{first}.{last}` pattern and is not a required argument.

Install the mitmproxy cert, set the proxy in your browser, go to google and/or bing and search (make sure to include the `/in`):

`site:linkedin.com/in "Target Company Name"`

Emails will be dumped to `emails.txt` in the specified format, and passed to Atomizer for spraying.


### Aerosol

Scrapes all text from the target website and sends it to [AWS Comprehend](https://aws.amazon.com/comprehend/) for analysis to generate custom wordlists for password spraying.

**Still a work in progress**

#### Usage

```
mitmdump -s aerosol.py --set domain=domain.com
```
