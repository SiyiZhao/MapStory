"""项目常量定义。"""

DEFAULT_DB = "data/mapstory.db"
DEFAULT_DB_PATH = DEFAULT_DB
DEFAULT_TIMEZONE = "Asia/Shanghai"
DEFAULT_LOCATION_RADIUS = 100
DEFAULT_PAGE_SIZE = 20

PRIORITY_FACT = "史实"
PRIORITY_QUESTIONABLE = "史实（存疑）"
PRIORITY_CUSTOM = "自设"
PRIORITY_DELETED = "史实（删减）"

PRIORITY_CHOICES = {
    "fact": PRIORITY_FACT,
    "doubt": PRIORITY_QUESTIONABLE,
    "fanon": PRIORITY_CUSTOM,
    "abridged_fact": PRIORITY_DELETED,
}

PRIORITY_LABELS = set(PRIORITY_CHOICES.values())

EVENT_COLUMNS = [
    "id",
    "time",
    "time_note",
    "lat",
    "lon",
    "location_note",
    "persons",
    "event",
    "priority",
    "remark",
]
