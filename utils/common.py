from datetime import datetime
from zoneinfo import ZoneInfo
from config import config


def get_current_datetime():
    return datetime.now(ZoneInfo(config.TIMEZONE))
