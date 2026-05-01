from langchain.tools import tool
from datetime import datetime
from databaseShared import BOOKING, SPECIALDB

@tool
def check_table_availability(date: str, time: str, brach: str) -> str:
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
        # Validate branch exists
        branch_id = brach.lower().strip()
        valid_branches = [key.lower() for key in SPECIALDB.keys()]
        
        if branch_id not in valid_branches:
            return f"Invalid branch. Available branches: {', '.join(SPECIALDB.keys())}"
        
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return "Invalid date format. Please use yyyy-mm-dd"
        
        try:
            datetime.strptime(time, "%H:%M")
        except ValueError:
            return "Invalid time format. Please use hh:mm"
        
        booking_key = f"{branch_id}_{date}_{time}"
        
        conflicting_bookings = [
            b for b in BOOKING 
            if b.get("branch", "").lower() == branch_id 
            and b.get("date") == date 
            and b.get("time") == time
        ]
        
        if conflicting_bookings:
            if len(conflicting_bookings) >= 5:  
                return f"No tables available at {branch_id} on {date} at {time}. Please try a different time."
            else:
                available_tables = 5 - len(conflicting_bookings)
                return f"Limited availability at {branch_id} on {date} at {time}. {available_tables} table(s) still available."
        else:
            return f"Tables are available at {branch_id} on {date} at {time}. You can proceed with your reservation."
    
    except Exception as e:
        return f"Error checking availability: {str(e)}"