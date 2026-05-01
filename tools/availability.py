"""
NovaBite- tool availabailty
Check table availability tool implementation"""

from datetime import datetime
from langchain.tools import StructuredTool
from .schemas import CheckAvailabilityInput, AvailabilityResponse, TableSize, BranchName
from .databaseShared import BOOKING, SPECIALDB

def check_table_availability(date: str, time: str, branch: str) -> dict:
    """
    Check the availability of a branch at a specific date and time.
    
    Args:
        date: Date to check availability (yyyy-mm-dd format)
        time: Time to check availability (hh:mm format)
        branch: Branch to check availability for
    
    Returns:
        dict: Availability status in AvailabilityResponse format
    """
    try:
        branchId = branch.lower().strip()
        validBranches = [key.lower() for key in SPECIALDB.keys()]
        branchKey = None
        for key in SPECIALDB.keys():
            if key.lower() == branchId:
                branchKey = key
                break
        
        if branchId not in validBranches:
            return {
                "status": "error",
                "branch": branch,
                "date": date,
                "time": time,
                "availableCount": 0,
                "availableSizes": [],
                "message": f"Invalid branch. Available branches: {', '.join(SPECIALDB.keys())}"
            }
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return {
                "status": "error",
                "branch": branch,
                "date": date,
                "time": time,
                "availableCount": 0,
                "availableSizes": [],
                "message": "Invalid date format. Please use yyyy-mm-dd"
            }
    
        try:
            datetime.strptime(time, "%H:%M")
        except ValueError:
            return {
                "status": "error",
                "branch": branch,
                "date": date,
                "time": time,
                "availableCount": 0,
                "availableSizes": [],
                "message": "Invalid time format. Please use hh:mm"
            }
        
        maxTablesPerSlot = 5
        conflictingBookings = [
            b for b in BOOKING
            if b.get("branch", "").lower() == branchId
            and b.get("date") == date
            and b.get("time") == time
            and b.get("status") == "confirmed"
        ]
        
        bookedTableCount = len(conflictingBookings)
        availableTableCount = maxTablesPerSlot - bookedTableCount
        
        if availableTableCount == 0:
            status = "unavailable"
            availableSizes = []
        elif availableTableCount < 2:
            status = "limited"
            availableSizes = ["2-top"]
        else:
            status = "available"
            availableSizes = ["2-top", "4-top", "6-top"]
        
        response = {
            "status": status,
            "branch": branch,
            "date": date,
            "time": time,
            "availableCount": availableTableCount,
            "availableSizes": availableSizes,
            "message": _build_availability_message(branch, date, time, status, availableTableCount),
            "nextAvailableSlot": None
        }
        
        return response
    
    except Exception as e:
        return {
            "status": "error",
            "branch": branch,
            "date": date,
            "time": time,
            "availableCount": 0,
            "availableSizes": [],
            "message": f"Error checking availability: {str(e)}"
        }


def _build_availability_message(branch: str, date: str, time: str, status: str, count: int) -> str:
    """Build a human-readable availability message"""
    if status == "available":
        return f"✓ Tables are available at {branch} on {date} at {time}. {count} table(s) available. You can proceed with your reservation."
    elif status == "limited":
        return f"⚠ Limited availability at {branch} on {date} at {time}. Only {count} table available. Book now!"
    elif status == "unavailable":
        return f"✗ No tables available at {branch} on {date} at {time}. Please try a different time or date."
    else:
        return "Unable to determine availability. Please try again."

checkTableAvailabilityTool = StructuredTool.from_function(
    func=check_table_availability,
    name="check_table_availability",
    description=(
        "Check table availability at a NovaBite branch for a specific date and time. "
        "Use when a customer wants to know if tables are available before booking. "
        "Returns available table count and sizes."
    ),
    args_schema=CheckAvailabilityInput,
    return_direct=False,
)