"""Today's special dish tool implementation"""

from datetime import datetime
from langchain.tools import StructuredTool
from .schemas import GetTodaySpecialInput, TodaySpecialResponse, BranchName
from .databaseShared import SPECIALDB

# Map weekday to special dishes for each branch
WEEKDAY_SPECIALS = {
    0: {  # Monday
        "nacrCity": {
            "startDish": "Vegan Pasta Primavera",
            "endDish": "Vegan Chocolate Cake",
            "additionalDish": "Vegan Caesar Salad",
            "price": 250
        },
        "ShroukCity": {
            "startDish": "Vegan Burger",
            "endDish": "Vegan Brownie",
            "additionalDish": "Vegan Greek Salad",
            "price": 200
        }
    },
    1: {  # Tuesday
        "nacrCity": {
            "startDish": "Grilled Vegetable Medley",
            "endDish": "Mango Sorbet",
            "additionalDish": "Hummus Trio",
            "price": 220
        },
        "ShroukCity": {
            "startDish": "Falafel Wrap",
            "endDish": "Pistachio Baklava",
            "additionalDish": "Tabbouleh Salad",
            "price": 190
        }
    },
    2: {  # Wednesday
        "nacrCity": {
            "startDish": "Eggplant Moussaka",
            "endDish": "Lemon Panna Cotta",
            "additionalDish": "Greek Salad",
            "price": 280
        },
        "ShroukCity": {
            "startDish": "Herb-Roasted Cauliflower",
            "endDish": "Date & Walnut Cake",
            "additionalDish": "Beets Salad",
            "price": 210
        }
    },
    3: {  # Thursday
        "nacrCity": {
            "startDish": "Mushroom Risotto",
            "endDish": "Tiramisu",
            "additionalDish": "Arugula Salad",
            "price": 290
        },
        "ShroukCity": {
            "startDish": "Spinach Pie",
            "endDish": "Coconut Pudding",
            "additionalDish": "Mixed Greens Salad",
            "price": 205
        }
    },
    4: {  # Friday
        "nacrCity": {
            "startDish": "Vegan Seafood Tacos",
            "endDish": "Passion Fruit Mousse",
            "additionalDish": "Rainbow Salad",
            "price": 310
        },
        "ShroukCity": {
            "startDish": "Pulled Jackfruit Sandwich",
            "endDish": "Avocado Cheesecake",
            "additionalDish": "Kale Salad",
            "price": 240
        }
    },
    5: {  # Saturday
        "nacrCity": {
            "startDish": "Herb-Crusted Tofu",
            "endDish": "Raspberry Cheesecake",
            "additionalDish": "Beet Salad",
            "price": 300
        },
        "ShroukCity": {
            "startDish": "Grilled Portobello Mushroom",
            "endDish": "Carrot Cake",
            "additionalDish": "Edamame",
            "price": 225
        }
    },
    6: {  # Sunday
        "nacrCity": {
            "startDish": "Stuffed Bell Peppers",
            "endDish": "Strawberry Shortcake",
            "additionalDish": "Couscous Salad",
            "price": 270
        },
        "ShroukCity": {
            "startDish": "Shakshuka",
            "endDish": "Kunafa",
            "additionalDish": "Fattoush Salad",
            "price": 230
        }
    }
}


def get_today_special(branch: str) -> dict:
    """
    Get today's special dish for a given branch.
    
    Args:
        branch: Branch name (e.g., "nacrCity", "ShroukCity")
    
    Returns:
        dict: Today's special in TodaySpecialResponse format
    """
    branchId = branch.strip().lower()
    
    # Validate branch exists
    validBranches = ["nacrCity".lower(), "ShroukCity".lower()]
    if branchId not in validBranches:
        return {
            "status": "error",
            "branch": branch,
            "weekday": "",
            "startDish": "",
            "endDish": "",
            "additionalDish": "",
            "message": f"Branch '{branch}' not found. Available branches: nacrCity, ShroukCity"
        }
    
    # Get today's weekday (0=Monday, 6=Sunday)
    today = datetime.now()
    weekday = today.weekday()
    weekdayNames = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekdayName = weekdayNames[weekday]
    
    # Get special for today
    todaysSpecials = WEEKDAY_SPECIALS.get(weekday, {})
    branchSpecial = todaysSpecials.get(branchId, {})
    
    if not branchSpecial:
        return {
            "status": "error",
            "branch": branch,
            "weekday": weekdayName,
            "startDish": "",
            "endDish": "",
            "additionalDish": "",
            "message": f"No special available for {branchId} on {weekdayName}"
        }
    
    response = {
        "status": "success",
        "branch": branch,
        "weekday": weekdayName,
        "startDish": branchSpecial.get("startDish", ""),
        "endDish": branchSpecial.get("endDish", ""),
        "additionalDish": branchSpecial.get("additionalDish", ""),
        "price": branchSpecial.get("price", 0),
        "message": f"Today's special at {branch}: {branchSpecial.get('startDish', '')} → {branchSpecial.get('endDish', '')} (EGP {branchSpecial.get('price', 0)})"
    }
    
    return response


# Create structured tool
getTodaySpecialTool = StructuredTool.from_function(
    func=get_today_special,
    name="get_today_special",
    description=(
        "Retrieve today's special dish menu for a NovaBite branch. "
        "Use when a customer asks about the special of the day. "
        "Returns starter, dessert, and side dish with pricing."
    ),
    args_schema=GetTodaySpecialInput,
    return_direct=False,
)
