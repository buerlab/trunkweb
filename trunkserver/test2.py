#encoding=utf-8
from datetime import datetime
import time
time1 = time.time()
print "time1",time1

def getWeekTimeStr(_time):
    a = datetime.fromtimestamp(_time)
    b = a.replace(a.year,a.month,a.day- a.weekday(),0,0,0,0)
    c = a.replace(a.year,a.month,a.day +6 - a.weekday(),0,0,0,0)

    b1 = time.strftime("t-%Y-%m-%d",b.timetuple())
    c1 = time.strftime(":%Y-%m-%d",c.timetuple())
    return b1 + c1



print 20042/1000

print "jjjjjjjjjj"