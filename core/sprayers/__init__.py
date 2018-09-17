import urllib3
from .lync import Lync
from .owa import OWA

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
