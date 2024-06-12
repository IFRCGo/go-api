from dateutil.relativedelta import relativedelta


def get_previous_months(date, no):
    """Return a list of tuples with
    (month, year)

    Parameters:
    date (date): date from which to calculate previous months
    no (int): number of months to get

    Returns:
    list<tuple>: List of tuples with (month_string, first_day, last_day)
        eg. [
            ('2021-05', datetime, datetime)
        ]
    """
    months = []
    for i in range(0, no):
        previous_month = date - relativedelta(months=i)
        first_day = previous_month - relativedelta(day=1)
        last_day = previous_month - relativedelta(day=31)
        month_string = f"{first_day.year}-{str(first_day.month).zfill(2)}"
        month = (
            month_string,
            first_day,
            last_day,
        )
        months.append(month)
    return months
