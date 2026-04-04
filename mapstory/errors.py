"""项目错误类型定义。"""


class MapStoryError(Exception):
    """MapStory 所有自定义异常的根类。"""


class InputValidationError(MapStoryError, ValueError):
    """输入数据校验失败。"""


class NotFoundError(MapStoryError, LookupError):
    """请求的资源不存在。"""


class DatabaseError(MapStoryError, RuntimeError):
    """数据库操作失败。"""


class TimeFormatError(MapStoryError, ValueError):
    """时间格式解析或转换失败。"""


class LocationError(MapStoryError, ValueError):
    """地理位置解析或转换失败。"""

