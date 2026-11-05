with open('apps/ipo/services.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace open/close dates for JIO
text = text.replace(
    '"symbol": "JIO",\n            "sector": "Telecom, Cloud & Digital Services",\n            "category": "Mainboard",\n            "status": "Open",\n            "open_date": date(2026, 10, 21),\n            "close_date": date(2026, 10, 23),',
    '"symbol": "JIO",\n            "sector": "Telecom, Cloud & Digital Services",\n            "category": "Mainboard",\n            "status": "Open",\n            "open_date": date(2026, 10, 24),\n            "close_date": date(2026, 10, 28),'
)

# Replace open/close dates for PARAS
text = text.replace(
    '"symbol": "PARAS",\n            "sector": "Healthcare Delivery & Hospitals",\n            "category": "Mainboard",\n            "status": "Open",\n            "open_date": date(2026, 10, 21),\n            "close_date": date(2026, 10, 23),',
    '"symbol": "PARAS",\n            "sector": "Healthcare Delivery & Hospitals",\n            "category": "Mainboard",\n            "status": "Open",\n            "open_date": date(2026, 10, 24),\n            "close_date": date(2026, 10, 27),'
)

with open('apps/ipo/services.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated dates in services.py successfully")
