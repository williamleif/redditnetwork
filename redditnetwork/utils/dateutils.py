import datetime 
from isoweek import Week
import calendar

def get_week(timestamp):
    timestamp = datetime.datetime.utcfromtimestamp(float(timestamp))
    date = timestamp.date()
    iso_info = date.isocalendar()
    week = iso_info[1] - 1
    return week

def get_week_timestamp(year, week):
    d = Week(year, week).monday()
    return calendar.timegm(d.timetuple())

def day_week(timestamp):
    timestamp = datetime.datetime.utcfromtimestamp(float(timestamp))
    date = timestamp.date()
    iso_info = date.isocalendar()
    week = iso_info[1] - 1
    day = week * 7 + iso_info[2] - 1
    return day, week

def month_year(timestamp):
    date = datetime.datetime.utcfromtimestamp(int(timestamp))
    return (date.year, date.month)

def month_year_add(month_year, increment):
    month_year = (month_year[0] + (increment + month_year[1] - 1) / 12,
        (month_year[1] + increment - 1) % 12 + 1)
    return month_year

def previous_month_year(month_year):
    month_year = (month_year[0], month_year[1]-1)
    if month_year[1] < 1:
        month_year= (month_year[0] - 1, 12)
    return month_year
