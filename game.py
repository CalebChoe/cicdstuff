import streamlit as st
import s3funcs
import json
import random
import os
from botocore.exceptions import ClientError

BUCKET_NAME = 'gamethingy732372894'

RESOURCES = [
    # (item, weight, min_amount, max_amount, emoji)
    ("stone",    50, 3, 8,  "🪨"),
    ("iron",     25, 2, 5,  "🔩"),
    ("gold",     12, 1, 3,  "🟡"),
    ("emerald",   7, 1, 2,  "💚"),
    ("ruby",      4, 1, 2,  "🔴"),
    ("diamond",   2, 1, 1,  "💎"),
]

ITEMS   = [r[0] for r in RESOURCES]
WEIGHTS = [r[1] for r in RESOURCES]

def get_from_s3(username):
    filename = f'data{username}.txt'
    s3funcs.download_file(BUCKET_NAME, filename, filename)
    if not os.path.exists(filename):
        return {"username": username, "inventory": {}}
    with open(filename, "r") as file:
        return json.loads(file.read())

def save_to_s3(data):
    filename = f'data{data["username"]}.txt'
    with open(filename, "w") as file:
        file.write(json.dumps(data, indent=4))
    s3funcs.upload_file(BUCKET_NAME, filename)

# --- UI ---
st.title("⛏️ Mining Game")

username = st.text_input("Username", value="caleb")

if st.button("Load / New Game"):
    st.session_state.data = get_from_s3(username)

if "data" in st.session_state:
    data = st.session_state.data
    st.subheader(f"Welcome, {data['username']}!")

    st.write("### Inventory")
    if data["inventory"]:
        for res in RESOURCES:
            item, _, _, _, emoji = res
            qty = data["inventory"].get(item, 0)
            if qty > 0:
                st.write(f"{emoji} **{item.capitalize()}**: {qty}")
    else:
        st.write("_Empty — start mining!_")

    if st.button("⛏️ Mine"):
        drops = []
        picks = random.choices(ITEMS, weights=WEIGHTS, k=random.randint(1, 3))
        for item in picks:
            _, _, lo, hi, emoji = next(r for r in RESOURCES if r[0] == item)
            amount = random.randint(lo, hi)
            data["inventory"][item] = data["inventory"].get(item, 0) + amount
            drops.append(f"{emoji} +{amount} {item}")
        st.success("  |  ".join(drops))
        st.session_state.data = data

    if st.button("💾 Save"):
        save_to_s3(data)
        st.success("Saved to S3!")