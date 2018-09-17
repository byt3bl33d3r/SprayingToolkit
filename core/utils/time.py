from datetime import timedelta, tzinfo

# https://stackoverflow.com/questions/19654578/python-utc-datetime-objects-iso-format-doesnt-include-z-zulu-or-zero-offset
# I have no clue what I'm doing here

class simple_utc(tzinfo):

    def tzname(self, **kwargs):
        return "UTC"

    def utcoffset(self, dt):
        return timedelta(0)
