import logging
from core.utils.messages import print_good, print_bad
import imapclient

class IMAP:
    def __init__(self, target):
        self.log = logging.getLogger('imapsprayer')
        self.valid_accounts = set()
        self.target = target
        self.O365 = True

    def shutdown(self):
        with open('imap_valid_accounts.txt', 'a+') as account_file:
            for pair in self.valid_accounts:
                account_file.write(' : '.join(pair) + '\n')

        self.log.info(print_good(f"Dumped {len(self.valid_accounts)} valid accounts to imap_valid_accounts.txt"))

    def auth_O365(self, username, password):
        log = logging.getLogger(f"auth_imap_O365({username})")
        try:
            server = imapclient.IMAPClient(self.target, port=993, ssl=True)
            server.login(username, password)
            self.valid_accounts.add((username, password))
            log.info(print_good(f"Found credentials: {username}:{password}"))
        except:
            log.info(print_bad(f"Authentication failed: {username}:{password} (Login failed)"))
            pass

    def __str__(self):
        return "IMAP"
