import math

class LocalTime:
    
    def __init__(self, h: int = 0, m: int = 0, s: int = 0, tz: int = 0):
        self.h: int = h
        self.m: int = m
        self.s: int = s
        self.tz: int = tz
    
    def set(self, h: int = 0, m: int = 0, s: int = 0):
        self.h = int(math.fabs(h) % 24) + self.tz
        self.m = int(math.fabs(m) % 60)
        self.s = int(math.fabs(s) % 60)
        
    def timestamp(self, t=None):
        if (t is None):
            return self.h*3600 + self.m*60 + self.s
        if (t < 0):
            import ntptime
            t = ntptime.time()
            ts = self.timestamp(t)
            return self.timestamp(ts)
        s = int(t % 60)
        m = int(t // 60 % 60)
        h = int(t // 3600 % 24)
        self.set(h, m, s)
        return self.timestamp()
        
    def __repr__(self):
        return f'T{self.h:02d}{self.m:02d}{self.s:02d}'
    
    def timeZone(self, tz: int = None):
        if (tz is not None):
            self.tz = int(tz) % 24
        return self.tz