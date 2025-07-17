# Common Recurrence Rules (RRULE) for Reminders

This page lists the most common iCalendar RRULE strings you can use for reminders and scheduling.
Each RRULE defines a pattern for how often your reminder repeats.

## What is an RRULE?
An RRULE (Recurrence Rule) follows the [iCalendar RFC 5545 standard](https://datatracker.ietf.org/doc/html/rfc5545) and tells your app how to repeat an event.

**Format Example:**  
`FREQ=DAILY;INTERVAL=1` means “every day.”

---

## Every Day
```text
FREQ=DAILY
```
Repeats every day.

---

## Every Week
```text
FREQ=WEEKLY
```
Repeats every week on the same day.

---

## Every Month (same day of month)
```text
FREQ=MONTHLY
```
Repeats every month on the same day (e.g., 15th).

---

## Every Year (same date)
```text
FREQ=YEARLY
```
Repeats once every year on the same month and day.

---

## Every Hour
```text
FREQ=HOURLY
```
Repeats every hour.

---

## Every Minute
```text
FREQ=MINUTELY
```
Repeats every minute.

---

## Every Weekday (Monday to Friday)
```text
FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR
```
Repeats every Monday, Tuesday, Wednesday, Thursday, and Friday.

---

## Every Monday
```text
FREQ=WEEKLY;BYDAY=MO
```
Repeats every Monday.

---

## Every 2 Weeks
```text
FREQ=WEEKLY;INTERVAL=2
```
Repeats every other week.

---

## Last Day of Every Month
```text
FREQ=MONTHLY;BYMONTHDAY=-1
```
Repeats on the last day of each month.

---

## 1st and 16th of Every Month
```text
FREQ=MONTHLY;BYMONTHDAY=1,16
```
Repeats on the 1st and 16th day of every month.

---

## 2nd Tuesday of Every Month
```text
FREQ=MONTHLY;BYDAY=2TU
```
Repeats on the second Tuesday of each month.

---

## First Workday of Each Month (Monday–Friday)
```text
FREQ=MONTHLY;BYDAY=MO,TU,WE,TH,FR;BYSETPOS=1
```
Repeats on the first Monday–Friday of each month (whichever comes first).

---

## Every Week on Monday, Wednesday, and Friday
```text
FREQ=WEEKLY;BYDAY=MO,WE,FR
```
Repeats every Monday, Wednesday, and Friday.

---

## Fourth Thursday in November (US Thanksgiving)
```text
FREQ=YEARLY;BYMONTH=11;BYDAY=4TH
```
Repeats on the fourth Thursday in November.

---

For advanced patterns, see the [RFC 5545 spec](https://datatracker.ietf.org/doc/html/rfc5545#section-3.8.5.3) or [iCalendar documentation](https://icalendar.org/iCalendar-RFC-5545/3-8-5-3-recurrence-rule.html).
