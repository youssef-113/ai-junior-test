"""Loyalty points tool implementation"""

import logging
from datetime import datetime
from langchain.tools import StructuredTool
from schemas import CheckLoyaltyPointsInput, LoyaltyPointsResponse, LoyaltyTier
from databaseShared import LOYALTYDB, PLANS

# Loyalty tier thresholds
LOYALTY_TIERS = [
    {
        "name": "base",
        "minPoints": 0,
        "maxPoints": 299,
        "discountPercent": 0,
        "perks": ["Free drink with every meal"]
    },
    {
        "name": "pro",
        "minPoints": 300,
        "maxPoints": 749,
        "discountPercent": 15,
        "perks": ["15% discount", "Free dessert monthly", "Priority booking"]
    },
    {
        "name": "premium",
        "minPoints": 750,
        "maxPoints": float('inf'),
        "discountPercent": 20,
        "perks": ["20% discount", "Priority reservations", "Free birthday meal"]
    }
]


def _get_tier(points: int) -> dict:
    """Determine loyalty tier based on points"""
    for tier in LOYALTY_TIERS:
        if tier["minPoints"] <= points <= tier["maxPoints"]:
            return tier
    return LOYALTY_TIERS[0] 


def _points_to_next_tier(points: int) -> int:
    """Calculate points needed to reach next tier"""
    for tier in LOYALTY_TIERS:
        if tier["minPoints"] <= points < tier["maxPoints"]:
            return tier["maxPoints"] - points
    return None 


def check_loyalty_points(userId: str) -> dict:
    """
    Return loyalty point balance, tier, and redemption info for a user.
    
    Args:
        userId: User's loyalty ID (e.g., NB-USR-0001)
    
    Returns:
        dict: Loyalty information in LoyaltyPointsResponse format
    """
    uid = userId.strip().upper()
    user = LOYALTYDB.get(uid)

    if not user:
        return {
            "status": "error",
            "userId": uid,
            "statusValue": "not_found",
            "loyaltyPoints": 0,
            "tier": "base",
            "message": f"User ID '{userId}' not found. Please verify your NovaBite loyalty ID.",
            "tip": "Your loyalty ID starts with 'NB-USR-' and was provided when you registered."
        }

    points = user.get("loyaltyPoints", 0)
    tier = _get_tier(points)
    pointsToNext = _points_to_next_tier(points)

    # Redemption calculation: 100 points = 50 EGP
    redeemableAmount = points // 100
    redeemableValueEgp = redeemableAmount * 50

    response = {
        "status": "success",
        "userId": uid,
        "statusValue": "found",
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "phone": user.get("phone", ""),
        "loyaltyPoints": points,
        "tier": tier["name"],
        "tierDiscountPercent": tier["discountPercent"],
        "tierPerks": tier["perks"],
        "redeemableValueEgp": redeemableValueEgp,
        "redemptionNote": "100 points = 50 EGP discount. Minimum redemption: 100 points.",
        "totalSpentEgp": user.get("totalSpentEgp", 0),
        "totalBookings": user.get("totalBookings", 0),
        "joinDate": user.get("joinDate", ""),
        "message": f"You have {points} loyalty points and are at {tier['name'].upper()} tier!"
    }

    if pointsToNext is not None:
        nextTierIndex = LOYALTY_TIERS.index(tier) + 1
        if nextTierIndex < len(LOYALTY_TIERS):
            nextTier = LOYALTY_TIERS[nextTierIndex]
            response["nextTier"] = nextTier["name"]
            response["pointsToNextTier"] = pointsToNext
    else:
        response["nextTier"] = None
        response["pointsToNextTier"] = None
        response["premiumNote"] = "You're at the highest tier — Premium!"

    return response


check_loyalty_points = StructuredTool.from_function(
    func=check_loyalty_points,
    name="check_loyalty_points",
    description=(
        "Check a customer's NovaBite loyalty points balance, tier, and redemption value. "
        "Use when a customer asks about their points, rewards, or membership tier. "
        "Input: userId (e.g., NB-USR-0001)."
    ),
    args_schema=CheckLoyaltyPointsInput,
    return_direct=False,
)