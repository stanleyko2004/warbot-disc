import datetime
from datetime import datetime, time, timedelta, timezone

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
    
    def get_current_start(self, now: datetime = datetime.now(timezone.utc)) -> datetime:
        if now.tzinfo is None or now.tzinfo.utcoffset(now) is None:
            raise ValueError('timezone aware timestamp needed')
        
        today = now.date()
        offset = (today.weekday() - self.weekday) % 7
        
        # will be the current day if today is the weekday
        prev_date = today - timedelta(days=offset)
        
        # subtract a week if a new war is supposed to start today but the start time hasn't passed
        if now.timetz() <= self.time:
            prev_date -= timedelta(days=7)
        
        # keep the same tzinfo as passed in
        return datetime.combine(prev_date, self.time).astimezone(now.tzinfo)
    
    def get_next_start(self, now: datetime = datetime.now(timezone.utc)) -> datetime:
        return self.get_current_start(now) + timedelta(days=7)
    
    def get_war_days(self, now: datetime = datetime.now(timezone.utc)) -> tuple[datetime, datetime, datetime]:
        return tuple(self.get_current_start(now) + timedelta(days=n*2) for n in range(3))

def main():
    # import zoneinfo
    # print(zoneinfo.available_timezones())
    PST = timezone(timedelta(hours=-8))
    MON, TUE, WED, THU, FRI, SAT, SUN = range(7)

    WAR_SCHEDULE = WarSchedule(WED, time(1, tzinfo=PST))
    print(WAR_SCHEDULE.get_war_days(datetime.now(timezone(timedelta(hours=-8)))))

if __name__ == '__main__':
    main()