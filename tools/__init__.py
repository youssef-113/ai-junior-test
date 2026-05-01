from .availability import check_availability_tool, book_table_tool
from .specials import get_today_special_tool
from .loyalty import check_loyalty_tool

ALL_TOOLS = [
    check_availability_tool,
    book_table_tool,
    get_today_special_tool,
    check_loyalty_tool,
]

__all__ = [
    "check_availability_tool",
    "book_table_tool",
    "get_today_special_tool",
    "check_loyalty_tool",
    "ALL_TOOLS",
]
