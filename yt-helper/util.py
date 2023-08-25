import datetime

def convert_date(in_date : str) -> datetime:
    if not in_date: return None
    try:
        y : str
        m : str
        d : str
        y, m, d = in_date.split("-")
        return datetime.datetime(int(y),int(m),int(d))
    except ValueError:
        raise Exception(f"Invalid date string [{in_date}], format must be YYYY-mm-dd")
