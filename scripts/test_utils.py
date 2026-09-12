from utils import clean_string, clean_price, summarize, normalize_list

print(clean_price("N/A"))
print(clean_price(""))
print(clean_price(None))
print(clean_price(15))

print(normalize_list([], clean_string))

orders = [
    {"city": None, "status": "delivered"},
    {"city": None, "status": "cancelled"},
    {"city": None, "status": "delivered"},
    {"city": None,    "status": "pending"},
]
print(summarize(orders, "city"))
