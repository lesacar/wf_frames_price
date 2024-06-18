import requests
import json
import time
import sys
import os
import pywmapi as wm

API_BASE_URL = "https://api.warframe.market/v1"

# Function to read the cached data and return a list of tuples
def load_cached_data(filename):
    with open(filename, 'r') as f:
        lines = f.read().splitlines()
    items = []
    for i in range(0, len(lines), 3):  # Adjusted range to account for item_name, item_id, url_name structure
        item_name = lines[i]
        url_name = lines[i+1]  # Read url_name directly from the file
        items.append((item_name, url_name))  # Store only item_name and url_name
    return items

# Function to fetch orders for each item and filter by user status "ingame" and order type "sell"
def fetch_item_orders(url_name):
    formatted_url_name = url_name.lower().replace(' ', '_').replace('prime_set', 'prime_set')  # Adjust if necessary
    
    with open("urls.txt", 'a') as urlsF:
        urlsF.write(formatted_url_name + '\n')

    response = requests.get(f"{API_BASE_URL}/items/{formatted_url_name}/orders")
    
    if response.status_code == 200:
        data = response.json()
        filtered_orders = [order for order in data['payload']['orders'] if order['user']['status'] == 'ingame' and order['order_type'] == 'sell']
        return filtered_orders
    else:
        print(f"Failed to fetch orders for {url_name}. Status code: {response.status_code}")
        return None


# Function to sort orders by price and get the three cheapest
def get_cheapest_orders(orders, num_orders=3):
    sorted_orders = sorted(orders, key=lambda x: x['platinum'])
    return sorted_orders[:num_orders]

# Make a GET request to fetch data from Warframe Market API
# This magic url basically contains only prime items, so it's easier to
# go 1 by 1 from here to detect warframe sets, rather then going over literally every item in the game
# which would take hours
url = "https://api.warframe.market/v1/tools/ducats"
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse JSON response
    data = response.json()
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")

# Create a set of ids from the first loop
ids_set = {item['item'] for item in data['payload']['previous_hour']}

# Retrieve items list using pywmapi
items_list = wm.items.list_items()

# Loop over items_list and check if each id is in ids_set and item name contains "Set"
if len(sys.argv) == 2:
    if sys.argv[1] == "update":
        tmpint = 0
        print("Updating prime warframes database")
        with open('cache.txt', 'w') as f0:
            for item in items_list:
                if item.id in ids_set and "Set" in item.item_name:
                    tmpitem = wm.items.get_item(item.url_name)
                    time.sleep(0.34)
                    if "warframe" in tmpitem[0].tags:
                        tmpint += 1
                        f0.write(item.item_name + '\n')
                        f0.write(item.url_name + '\n')  # Write url_name directly
                        f0.write(item.id + '\n')
                        print(item.item_name)
        print(f"All prime warframes ({tmpint}) should be up to date\nThe tool is now ready")
        print("Exiting... Run again without 'update' to use")
        exit(0)

cache_path = 'cache.txt'
if not os.path.exists(cache_path):
    print(f"The file '{cache_path}' does not exist.")
    print(f"Run the tool with 'python {sys.argv[0]} update' at least once, and every\ntime Warframe gets a new prime warframe")
    exit()  # Exit the program

# Save ids from the first loop to 1.txt
with open('1.txt', 'w') as f1:
    for item in data['payload']['previous_hour']:
        f1.write(item['item'] + '\n')

# Save item ids from the second loop to 2.txt
with open('2.txt', 'w') as f2:
    for item in items_list:
        f2.write(item.id + '\n')

# Load cached data
cached_items = load_cached_data('cache.txt')

# Dictionary to store cheapest orders for each item
cheapest_orders_dict = {}

# Fetch orders for each cached item and store the three cheapest orders
for item_name, url_name in cached_items:
    orders = fetch_item_orders(url_name)  # Pass only url_name to fetch_item_orders
    time.sleep(0.34)
    if orders:
        cheapest_orders = get_cheapest_orders(orders)
        # Store the cheapest order for this item
        if cheapest_orders:
            cheapest_order = cheapest_orders[0]  # Taking the cheapest order
            cheapest_orders_dict[item_name] = {
                'cheapest_platinum': cheapest_order['platinum'],
                'second_cheapest_platinum': cheapest_orders[1]['platinum'] if len(cheapest_orders) > 1 else None,
                'third_cheapest_platinum': cheapest_orders[2]['platinum'] if len(cheapest_orders) > 2 else None
            }

# make tuple array that stores the frame name and cheapest sell offer
list_of_cheapest_offers = []

# Print the item name and its cheapest order
list_of_cheapest_offers = []  # Initialize an empty list to store cheapest offers

for item_name, orders_info in cheapest_orders_dict.items():
    print(f"Item: {item_name}")
    print(f"Cheapest Order: {orders_info['cheapest_platinum']} platinum")
    list_of_cheapest_offers.append([item_name, orders_info['cheapest_platinum']])

    if orders_info['second_cheapest_platinum'] is not None:
        print(f"Second Cheapest Order: {orders_info['second_cheapest_platinum']} platinum")

    if orders_info['third_cheapest_platinum'] is not None:
        print(f"Third Cheapest Order: {orders_info['third_cheapest_platinum']} platinum")

    print("=" * 30)

# Write list_of_cheapest_offers to frames.txt
list_of_cheapest_offers.sort(key=lambda x: x[1], reverse=True)
with open("frames.txt", 'w') as tupleF:
    for item in list_of_cheapest_offers:
        tupleF.write(f"{item}\n")

print("=" * 30)
print("=" * 30)
print("=" * 30)
print("Done processing")
print("This program has outputted each prime frame set, with the 3 cheapest sell orders")
print("CHECK 'frames.txt' FOR THE SORTED PRIME FRAME SET PRICES")
print("Keep in mind that the 'frames.txt' file only contains the cheapest price\nwhich could be a troll, be sure to double check prices on wfm")
