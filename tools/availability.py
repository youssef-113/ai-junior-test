from langchain.tools import tool
from datetime import datetime

@tool
def check_table_availability(date: str, time:str , brach:str) -> str :
    """
    check the availability of a branch at a specific date format: yyyy-mm-dd and timeformat: hh:mm
    Args:
        date (str): the date to check the availability
        time (str): the time to check the availability
        brach (str): the branch to check the availability
    Returns:
        str: the availability status of the branch at the specified date and time

    """
    try:
        branchID = branch.lower().strip()
        



    except:
        return "Invalid date or time format. Please use yyyy-mm-dd for date and hh:mm for time."