# /// script
# dependencies = ["requests"]
# ///

import requests
import time
import csv

API = "https://api.warframe.market/v2"

def fetch(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.json()["data"]

items = fetch(f"{API}/items")
targets = {
    item["id"]: item["i18n"]["en"]["name"]
    for item in items
    if "warframe" in item["tags"] and "prime" in item["tags"] and "set" in item["tags"]
}

results = []
for item_id, name in targets.items():
    orders = fetch(f"{API}/orders/itemId/{item_id}")
    prices = sorted([
        o["platinum"] for o in orders
        if o["type"] == "sell" and o["user"]["status"] == "ingame"
    ])[:3]
    if prices:
        p1, p2, p3 = prices[0], prices[1] if len(prices) > 1 else "", prices[2] if len(prices) > 2 else ""
        results.append((name, p1, p2, p3))
    time.sleep(0.34)

results.sort(key=lambda x: x[1])

with open("frames.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["name", "cheapest", "second", "third"])
    w.writerows(results)

for r in results:
    print(f"{r[0]}: {r[1]}, {r[2]}, {r[3]}")
