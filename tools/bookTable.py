"""Book table tool implementation"""

import uuid
from datetime import datetime
from typing import Optional
from langchain.tools import StructuredTool
from .schemas import BookTableInput, BookingConfirmation, BranchName, SpecialEventType
from .databaseShared import BOOKING


def _generate_confirmation_id() -> str:
    """Generate a unique confirmation ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = str(uuid.uuid4())[:8].upper()
    return f"NB-{timestamp}-{random_suffix}"


def _is_table_available(branch: str, date: str, time: str) -> bool:
    """Check if tables are available for the given slot"""
    maxTablesPerSlot = 5
    
    bookingsForSlot = [
        b for b in BOOKING
        if b.get("branch", "").lower() == branch.lower()
        and b.get("date") == date
        and b.get("time") == time
        and b.get("status") == "confirmed"
    ]
    
    return len(bookingsForSlot) < maxTablesPerSlot


def _get_alternative_times(branch: str, date: str, originalTime: str) -> list:
    """Get alternative available times for the same date"""
    times = ["11:00", "12:00", "13:00", "18:00", "19:00", "20:00", "21:00"]
    alternatives = []
    
    for time in times:
        if time != originalTime and _is_table_available(branch, date, time):
            alternatives.append(time)
    
    return alternatives[:3]  # Return up to 3 alternatives


def book_table(
    guestName: str,
    userId: str,
    date: str,
    time: str,
    branch: str,
    partySize: int = 2,
    specialOccasion: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """
    Book a table at NovaBite restaurant.
    
    Args:
        guestName: Name of the guest
        userId: User's loyalty ID
        date: Reservation date (yyyy-mm-dd)
        time: Reservation time (hh:mm)
        branch: Branch name
        partySize: Number of guests (1-12)
        specialOccasion: Optional special occasion (birthday, anniversary, etc.)
        notes: Optional special requests
    
    Returns:
        dict: Booking confirmation in BookingConfirmation format
    """
    branchId = branch.strip().lower()
    validBranches = ["nacrCity".lower(), "ShroukCity".lower()]
    
    if branchId not in validBranches:
        return {
            "status": "failed",
            "confirmationId": None,
            "guestName": guestName,
            "branch": branch,
            "date": date,
            "time": time,
            "partySize": partySize,
            "message": f"Invalid branch. Available branches: nacrCity, ShroukCity"
        }
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return {
            "status": "failed",
            "confirmationId": None,
            "guestName": guestName,
            "branch": branch,
            "date": date,
            "time": time,
            "partySize": partySize,
            "message": "Invalid date format. Use yyyy-mm-dd"
        }
    
    try:
        datetime.strptime(time, "%H:%M")
    except ValueError:
        return {
            "status": "failed",
            "confirmationId": None,
            "guestName": guestName,
            "branch": branch,
            "date": date,
            "time": time,
            "partySize": partySize,
            "message": "Invalid time format. Use hh:mm"
        }

    # Validate party size
    if partySize < 1 or partySize > 12:
        return {
            "status": "failed",
            "confirmationId": None,
            "guestName": guestName,
            "branch": branch,
            "date": date,
            "time": time,
            "partySize": partySize,
            "message": "Party size must be between 1 and 12"
        }

    if not _is_table_available(branchId, date, time):
        alternatives = _get_alternative_times(branchId, date, time)
        return {
            "status": "unavailable",
            "confirmationId": None,
            "guestName": guestName,
            "branch": branch,
            "date": date,
            "time": time,
            "partySize": partySize,
            "message": f"No tables available at {time}. Please try another time.",
            "alternativeTimes": alternatives if alternatives else None
        }
    
    # Create booking record
    confirmationId = _generate_confirmation_id()
    
    booking = {
        "confirmationId": confirmationId,
        "userId": userId,
        "guestName": guestName,
        "branch": branch,
        "date": date,
        "time": time,
        "partySize": partySize,
        "specialOccasion": specialOccasion,
        "notes": notes,
        "createdAt": datetime.now().isoformat(),
        "status": "confirmed"
    }
    
    # Add to booking database
    BOOKING.append(booking)
    
    response = {
        "status": "confirmed",
        "confirmationId": confirmationId,
        "guestName": guestName,
        "branch": branch,
        "date": date,
        "time": time,
        "partySize": partySize,
        "message": f"✓ Booking confirmed! Your confirmation ID is {confirmationId}. "
                   f"A table for {partySize} at {branch} on {date} at {time}. "
                   f"You'll receive a confirmation SMS shortly."
    }
    
    if specialOccasion:
        response["specialOccasion"] = specialOccasion
        response["occasionMessage"] = f"We'll make sure to celebrate your {specialOccasion}!"
    
    return response


# Create structured tool
bookTableTool = StructuredTool.from_function(
    func=book_table,
    name="book_table",
    description=(
        "Book a table at NovaBite restaurant for a specified date, time, and branch. "
        "Use when a customer wants to make a reservation. "
        "Includes support for special occasions like birthdays or anniversaries."
    ),
    args_schema=BookTableInput,
    return_direct=False,
)
