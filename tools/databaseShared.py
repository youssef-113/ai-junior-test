"""this is for the database shared for tools to use it and share the data between them"""

BOOKING = []

LOYALTYDB = {
    "USR0001": {
        "name": "youssef bassiony ",
        "email": "youssef@email.com",
        "phone": "01001234567",
        "loyaltyPoints": 450,
        "tier": "pro",
        "totalBookings": 12,
        "totalSpentEgp": 2500,
        "joinDate": "2023-01-15"
    },
    "USR0002": {
        "name": "yossef abdallah",
        "email": "youssefA@email.com",
        "phone": "01234567890",
        "loyaltyPoints": 850,
        "tier": "premium",
        "totalBookings": 25,
        "totalSpentEgp": 4800,
        "joinDate": "2022-06-20"
    },
    "USR0003": {
        "name": "youssef hassan",
        "email": "youssefH@email.com",
        "phone": "01556789012",
        "loyaltyPoints": 120,
        "tier": "base",
        "totalBookings": 3,
        "totalSpentEgp": 450,
        "joinDate": "2024-11-01"
    }
}

SPECIALDB = {
    "nacrCity" : {
        "startwith" : "Vegan Pasta Primavera",
        "endwith" : "Vegan Chocolate Cake",
        "additional" : "Vegan Caesar Salad",
    },
    "ShroukCity" : {
        "startwith" : "Vegan Burger",
        "endwith" : "Vegan Brownie",
        "additional" : "Vegan Greek Salad",
    }

}

PLANS = {
    "base":   "no discount on food just a drink free with every meal",
    "pro":     "15% discount + free dessert monthly",
    "premium": "20% discount + priority reservations + free birthday meal",
}

EVENTS ={
    "birthday" : "Celebrate your special day with us! Enjoy a complimentary birthday meal and a personalized dessert on the house."
                " Make your reservation today and let us make your birthday unforgettable!",
    "anniversary" : "Celebrate your love with us! Enjoy a romantic dinner for two with a complimentary bottle of wine and a special dessert."
                     " Book your table now and make your anniversary unforgettable",
    "holiday" : "Celebrate the holidays with us! Enjoy a festive meal with special holiday-themed dishes and a complimentary dessert.",             
    "EidDay" : "Celebrate Eid with us! Enjoy a special Eid menu featuring traditional dishes and a complimentary dessert."
                " Book your table now and make your Eid celebration unforgettable!",

}