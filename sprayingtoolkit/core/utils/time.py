import time
from datetime import datetime
from datetime import timedelta, tzinfo
from sprayingtoolkit.core.utils.messages import print_info

# https://stackoverflow.com/questions/19654578/python-utc-datetime-objects-iso-format-doesnt-include-z-zulu-or-zero-offset
# I have no clue what I'm doing here
class simple_utc(tzinfo):

    def tzname(self, **kwargs):
        return "UTC"

    def utcoffset(self, dt):
        return timedelta(0)


# https://codereview.stackexchange.com/questions/199743/countdown-timer-in-python
def countdown_timer(hours, minutes, seconds, now=datetime.now):
    delay = timedelta(
        hours=int(hours),
        minutes=int(minutes),
        seconds=int(seconds)
    )

    target = now()

    one_second_later = timedelta(seconds=1)

    try:
        for remaining in range(int(delay.total_seconds()), 0, -1):
            target += one_second_later
            print(print_info(f"{timedelta(seconds=remaining - 1)} remaining until next spray"), end="\r")
            duration = (target - now()).total_seconds()
            if duration > 0: time.sleep(duration)
    except KeyboardInterrupt:
        return False
    return True

def get_utc_time():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
