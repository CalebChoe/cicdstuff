import boto3
import s3funcs
import json
import time, random
from botocore.exceptions import ClientError

BUCKET_NAME = 'gamethingy732372894'

data = {
    "username": "",
    "inventory": {},
    "hp": 30,
    "max_hp": 30,
    "atk": 4,
    "def": 1,
    "gold": 10,
    "floor": 1,
}

# ── Inventory ──────────────────────────────────────────────

def inv_add(item, amount=1):
    data["inventory"][item] = data["inventory"].get(item, 0) + amount

def inv_remove(item, amount=1):
    data["inventory"][item] -= amount
    if data["inventory"][item] <= 0:
        del data["inventory"][item]

def inv_show():
    if not data["inventory"]:
        print("  (empty)")
    else:
        for item, qty in data["inventory"].items():
            print(f"  {item} x{qty}")

# ── S3 ─────────────────────────────────────────────────────

def get_from_s3():
    global data
    filename = f'data{data["username"]}.txt'
    try:
        s3funcs.download_file(BUCKET_NAME, filename, filename)
        with open(filename, "r") as file:
            data = json.loads(file.read())
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
            pass  # New player, keep defaults
        else:
            raise

def save_to_s3():
    filename = f'data{data["username"]}.txt'
    json_string = json.dumps(data, indent=4)
    with open(filename, "w") as file:
        file.write(json_string)
    s3funcs.upload_file(BUCKET_NAME, filename)

# ── Helpers ────────────────────────────────────────────────

def hr():
    print("\n" + "─" * 40)

def prompt(options):
    """Show numbered options and return the chosen index (0-based)."""
    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {opt}")
    while True:
        choice = input("\n> ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return int(choice) - 1
        print("Invalid choice.")

ITEMS = {
    "health potion":  {"desc": "Restore 15 HP"},
    "iron sword":     {"desc": "+3 ATK (equip)", "equip": "atk", "val": 3},
    "steel sword":    {"desc": "+6 ATK (equip)", "equip": "atk", "val": 6},
    "leather armor":  {"desc": "+2 DEF (equip)", "equip": "def", "val": 2},
    "chain mail":     {"desc": "+4 DEF (equip)", "equip": "def", "val": 4},
    "smoke bomb":     {"desc": "Guarantees escape from combat"},
    "power gem":      {"desc": "+2 ATK permanently"},
}

SHOP = [
    ("health potion", 8),
    ("iron sword",   15),
    ("steel sword",  30),
    ("leather armor",12),
    ("chain mail",   25),
    ("smoke bomb",   10),
]

ENEMIES = [
    {"name": "Slime",       "hp": 8,  "atk": 2, "def": 0, "gold": (2, 5),   "loot": None},
    {"name": "Goblin",      "hp": 12, "atk": 4, "def": 1, "gold": (3, 7),   "loot": ("health potion", 0.3)},
    {"name": "Skeleton",    "hp": 15, "atk": 5, "def": 2, "gold": (4, 9),   "loot": ("smoke bomb", 0.2)},
    {"name": "Dark Knight", "hp": 28, "atk": 8, "def": 4, "gold": (8, 16),  "loot": ("power gem", 0.25)},
    {"name": "Dragon",      "hp": 50, "atk":14, "def": 6, "gold": (20, 40), "loot": ("steel sword", 1.0)},
]

FLOOR_NAMES = {
    1: "The Entrance Hall",
    2: "Fungal Caverns",
    3: "Bone Crypts",
    4: "Infernal Depths",
    5: "The Dragon's Lair",
}

# ── Combat ─────────────────────────────────────────────────

def combat(enemy):
    e = dict(enemy)  # copy so original is unchanged
    e_hp = e["hp"]
    print(f"\n  A {e['name']} appears!  HP:{e_hp}  ATK:{e['atk']}  DEF:{e['def']}")

    while True:
        hr()
        print(f"  Your HP: {data['hp']}/{data['max_hp']}   Enemy HP: {e_hp}/{e['hp']}")
        inv_show()
        choice = prompt(["Attack", "Use item", "Flee"])

        if choice == 0:  # Attack
            dmg = max(1, data["atk"] - e["def"] + random.randint(-1, 2))
            e_hp -= dmg
            print(f"  You hit the {e['name']} for {dmg} damage.")
            if e_hp <= 0:
                gold = random.randint(*e["gold"])
                data["gold"] += gold
                print(f"  The {e['name']} is defeated! You find {gold} gold.")
                if e["loot"]:
                    item, chance = e["loot"]
                    if random.random() < chance:
                        inv_add(item)
                        print(f"  Dropped: {item}!")
                return True  # won

        elif choice == 1:  # Use item
            use_item_menu()
            if data["hp"] <= 0:
                return False

        elif choice == 2:  # Flee
            if data["inventory"].get("smoke bomb", 0) > 0:
                inv_remove("smoke bomb")
                print("  You throw a smoke bomb and escape!")
                return False
            elif random.random() < 0.5:
                print("  You escape into the shadows.")
                return False
            else:
                print("  You failed to flee!")

        # Enemy attacks
        if e_hp > 0:
            dmg = max(1, e["atk"] - data["def"] + random.randint(-1, 2))
            data["hp"] -= dmg
            print(f"  The {e['name']} hits you for {dmg} damage. ({data['hp']} HP left)")
            if data["hp"] <= 0:
                data["hp"] = 0
                print("  You have been slain...")
                return False

# ── Items ──────────────────────────────────────────────────

def use_item_menu():
    usable = [(item, qty) for item, qty in data["inventory"].items() if item in ITEMS]
    if not usable:
        print("  You have nothing to use.")
        return
    print("\n  Use which item? (0 to cancel)")
    for i, (item, qty) in enumerate(usable, 1):
        print(f"  [{i}] {item} x{qty} — {ITEMS[item]['desc']}")
    raw = input("\n> ").strip()
    if not raw.isdigit() or int(raw) == 0:
        return
    idx = int(raw) - 1
    if idx >= len(usable):
        return
    item, _ = usable[idx]
    apply_item(item)

def apply_item(item):
    if item == "health potion":
        healed = min(data["max_hp"] - data["hp"], 15)
        data["hp"] += healed
        inv_remove(item)
        print(f"  You drink a health potion. +{healed} HP.")
    elif item == "power gem":
        data["atk"] += 2
        inv_remove(item)
        print("  The gem pulses. +2 ATK permanently!")
    elif ITEMS[item].get("equip"):
        slot = ITEMS[item]["equip"]
        val  = ITEMS[item]["val"]
        key  = f"equipped_{slot}"
        if data.get(key) == item:
            data[slot] -= val
            data[key] = None
            print(f"  You unequip the {item}.")
        else:
            if data.get(key):
                old = data[key]
                data[slot] -= ITEMS[old]["val"]
            data[slot] += val
            data[key] = item
            print(f"  You equip the {item}. {ITEMS[item]['desc']}.")
    else:
        print(f"  Can't use {item} here.")

# ── Shop ───────────────────────────────────────────────────

def visit_shop():
    hr()
    print("  A merchant sits in the shadows.\n")
    while True:
        print(f"  Your gold: {data['gold']}")
        options = [f"{name}  ({cost}g)  — {ITEMS[name]['desc']}" for name, cost in SHOP]
        options.append("Leave")
        choice = prompt(options)
        if choice == len(SHOP):
            break
        name, cost = SHOP[choice]
        if data["gold"] < cost:
            print("  Not enough gold.")
        else:
            data["gold"] -= cost
            inv_add(name)
            print(f"  Bought {name}.")

# ── Explore ────────────────────────────────────────────────

steps = 0

def explore():
    global steps
    steps += 1
    hr()

    roll = random.random()
    if steps % 8 == 0:
        room = "boss"
    elif roll < 0.45:
        room = "enemy"
    elif roll < 0.60:
        room = "loot"
    elif roll < 0.72:
        room = "shop"
    elif roll < 0.82:
        room = "rest"
    else:
        room = "empty"

    if room == "empty":
        print("  The room is quiet. Cobwebs drift in a cold breeze.")

    elif room == "loot":
        loot_table = ["health potion", "health potion", "leather armor", "iron sword", "smoke bomb"]
        item = random.choice(loot_table)
        gold = random.randint(3, 12)
        data["gold"] += gold
        inv_add(item)
        print(f"  You find a chest! Inside: {item} and {gold} gold.")

    elif room == "shop":
        visit_shop()

    elif room == "rest":
        print(f"  A campfire glows ahead. Rest here? (costs 10 gold, you have {data['gold']})")
        if data["gold"] >= 10:
            c = prompt(["Rest (10g)", "Move on"])
            if c == 0:
                data["gold"] -= 10
                healed = random.randint(12, 18)
                data["hp"] = min(data["max_hp"], data["hp"] + healed)
                print(f"  You rest. +{healed} HP.")
        else:
            print("  You can't afford to rest.")

    elif room in ("enemy", "boss"):
        pool = [ENEMIES[4]] if room == "boss" else ENEMIES[:4]
        tier = min(data["floor"] - 1, len(pool) - 1)
        enemy = random.choice(pool[:tier + 1])
        won = combat(enemy)
        if not won and data["hp"] <= 0:
            return False  # dead
        if won and enemy["name"] == "Dragon":
            hr()
            print("  The dragon falls. The dungeon shakes.")
            print("  ★  You have conquered The Hollow Depths!  ★")
            return "win"
        if won and steps % 8 == 0:
            data["floor"] += 1
            print(f"\n  You descend deeper — Floor {data['floor']}: {FLOOR_NAMES.get(data['floor'], 'Unknown Depths')}")

    return True  # alive

# ── Main loop ──────────────────────────────────────────────

def show_status():
    hr()
    print(f"  Floor {data['floor']} — {FLOOR_NAMES.get(data['floor'], '???')}")
    print(f"  HP {data['hp']}/{data['max_hp']}  ATK {data['atk']}  DEF {data['def']}  Gold {data['gold']}")
    print("  Inventory:")
    inv_show()

def main():
    print("\n  THE HOLLOW DEPTHS\n")
    data["username"] = input("  Enter your name, adventurer: ").strip() or "hero"
    print("\n  Loading save data...")
    get_from_s3()
    print(f"  Welcome, {data['username']}.")

    while True:
        show_status()
        choice = prompt(["Explore", "Use item", "Save & quit"])

        if choice == 0:
            result = explore()
            if result == "win" or result is False:
                save_to_s3()
                break

        elif choice == 1:
            use_item_menu()

        elif choice == 2:
            save_to_s3()
            print("  Progress saved. Farewell.\n")
            break

if __name__ == "__main__":
    main()