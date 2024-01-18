import datetime
from datetime import datetime, time, timedelta, timezone
from itertools import takewhile

class WarSchedule:
    
    def __init__(self, weekday: int, time: time):
        """
        Args:
            weekday (int): starting weekday
            time (time): starting time. must be timezone aware
        """
        if time.tzinfo is None or time.tzinfo.utcoffset(None) is None:
            raise ValueError('time must be timezone aware')
        self.weekday = weekday
        self.time = time
    
    def get_current_start(self, now: datetime = None) -> datetime:
        now = _process_datetime_input(now)
        
        today = now.date()
        offset = (today.weekday() - self.weekday) % 7
        prev_date = today - timedelta(days=offset) # will be the current day if today is the weekday
        
        # subtract a week if a new war is supposed to start today but the start time hasn't passed
        if offset == 0 and now.timetz() <= self.time:
            prev_date -= timedelta(days=7)
        
        # return as unaware utc datetime
        return _format_datetime(datetime.combine(prev_date, self.time))
    
    def get_next_start(self, now: datetime = None) -> datetime:
        return self.get_current_start(now) + timedelta(days=7)
    
    def get_current_war_day(self, now: datetime = None) -> datetime:
        now = _format_datetime(_process_datetime_input(now))
        *_, war_day = takewhile(lambda wd: wd < now, WarSchedule.get_war_days(self.get_current_start(now)))
        # for war_day in WarSchedule.get_war_days(self.get_current_start(now)):
        #     if now - war_day < timedelta(days=1):
        #         return war_day
        return war_day
    
    @staticmethod
    def get_war_days(start: datetime) -> tuple[datetime, datetime, datetime]:
        return tuple(start + timedelta(days=n*2) for n in range(3))

def _process_datetime_input(input: datetime) -> datetime:
    """ensures offset-aware and utc"""
    # use current time by default
    if input is None:
        input = datetime.utcnow()
    
    # add utc tzinfo
    if input.tzinfo is None or input.tzinfo.utcoffset(input) is None: # unaware
        input = input.replace(tzinfo=timezone.utc)
    else:
        input = input.astimezone(timezone.utc)
    
    return input

def _format_datetime(output: datetime) -> datetime:
    """convert to utc and strip tzinfo"""
    return output.astimezone(timezone.utc).replace(tzinfo=None)

def main():
    # import zoneinfo
    # print(zoneinfo.available_timezones())
    PST = timezone(timedelta(hours=-8))
    MON, TUE, WED, THU, FRI, SAT, SUN = range(7)

    WAR_SCHEDULE = WarSchedule(WED, time(1, tzinfo=PST))
    print(WarSchedule.get_war_days(WAR_SCHEDULE.get_current_start()))
    print(_format_datetime(datetime.now()) - WAR_SCHEDULE.get_current_war_day())

if __name__ == '__main__':
    main()