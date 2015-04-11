from datetime import datetime, timedelta, tzinfo


class UTC(tzinfo):
    """Represents the Co-ordinated Universal Time zone."""
    __OFFSET = timedelta(0)

    def utcoffset(self, date_time):
        """Return the offset (in minutes) from UTC."""
        return self.__OFFSET

    def dst(self, date_time):
        """Return the offset (in minutes) from UTC when daylight-savings time is in effect."""
        return self.__OFFSET

    def tzname(self, date_time):
        """Return the name of this timezone."""
        return 'UTC'

utc = UTC()


def to_epoch(dt):
    """Convert a datetime to the number of second from epoch (1 January 1970)."""
    return (dt - _epoch).total_seconds()

_epoch = datetime(1970, 1, 1, tzinfo=utc)
