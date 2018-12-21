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
    atomizer (lync|owa) <target> <password> <userfile> [--threads THREADS] [--debug]
    atomizer (lync|owa) <target> --csvfile CSVFILE [--user-row-name NAME] [--pass-row-name NAME] [--threads THREADS] [--debug]
    atomizer (lync|owa) <target> --user-as-pass USERFILE [--threads THREADS] [--debug]
    atomizer (lync|owa) <target> --recon [--debug]
    atomizer -h | --help
    atomizer -v | --version

Arguments:
    target     target domain or url
    password   password to spray
    userfile   file containing usernames (one per line)

Options:
    -h, --help               show this screen
    -v, --version            show version
    -c, --csvfile CSVFILE    csv file containing usernames and passwords
    -t, --threads THREADS    number of concurrent threads to use [default: 3]
    -d, --debug              enable debug output
    --recon                  only collect info, don't password spray
    --user-row-name NAME     username row title in CSV file [default: Email Address]
    --pass-row-name NAME     password row title in CSV file [default: Password]
    --user-as-pass USERFILE  use the usernames in the specified file as the password (one per line)
```

#### Examples

```bash
python atomizer.py owa contoso.com 'Fall2018' emails.txt
```

```bash
python atomizer.py lync contoso.com 'Fall2018' emails.txt
```

```bash
python atomizer lync contoso.com --csvfile accounts.csv
```

```bash
python atomizer lync contoso.com --user-as-pass usernames.txt
```

```bash
python atomizer owa 'https://owa.contoso.com/autodiscover/autodiscover.xml' --recon
```

### Vaporizer

A port of [@OrOneEqualsOne](https://twitter.com/OrOneEqualsOne)'s [GatherContacts](https://github.com/clr2of8/GatherContacts) Burp extension to [mitmproxy](https://mitmproxy.org/) with some improvements.

Scrapes Google and Bing for LinkedIn profiles, automatically generates emails from the profile names using the specified pattern and performes password sprays in real-time.

(Built on top of Atomizer)

#### Examples

```bash
mitmdump -s vaporizer.py --set sprayer=(lync|owa) --set domain=domain.com --set target=<domain or url to spray> --set password=password --set email_format='{f}.{last}'
```

By default `email_format` is set to `{first}.{last}` pattern and is not a required argument.

The `domain` parameter is the domain to use for generating emails from names, the `target` parameter is the domain or url to password spray

Install the mitmproxy cert, set the proxy in your browser, go to google and/or bing and search (make sure to include the `/in`):

`site:linkedin.com/in "Target Company Name"`

Emails will be dumped to `emails.txt` in the specified format, and passed to Atomizer for spraying.


### Aerosol

Scrapes all text from the target website and sends it to [AWS Comprehend](https://aws.amazon.com/comprehend/) for analysis to generate custom wordlists for password spraying.

**Still a work in progress**

#### Usage

```bash
mitmdump -s aerosol.py --set domain=domain.com
```

### Spindrift

Converts names to active directory usernames (e.g `Alice Eve` => `CONTOSO\aeve`)

#### Usage

```
Usage:
    spindrift [<file>] [--target TARGET | --domain DOMAIN] [--format FORMAT]

Arguments:
    file    file containing names, can also read from stdin

Options:
    --target TARGET   optional domain or url to retrieve the internal domain name from OWA
    --domain DOMAIN   manually specify the domain to append to each username
    --format FORMAT   username format [default: {f}{last}]
```

#### Examples

Reads names from STDIN, `--domain` is used to specify the domain manually:

```bash
cat names.txt | ./spindrift.py --domain CONTOSO
```

Reads names from `names.txt`, `--target` dynamically grabs the internal domain name from OWA (you can give it a domain or url)

```bash
python spindrift.py names.txt --target contoso.com
```
