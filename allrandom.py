import requests
import random
import threading
import itertools
import sys
import time
import json
import os
from colorama import Fore, Style, init
# pip install -r requirements.txt

# Initialize colorama
init(autoreset=True)

SAVE_FILE = "checked_killers.json"

# Spinner for loading screen
def start_spinner(message, stop_event):
    spinner = itertools.cycle(['|', '/', '-', '\\'])
    while not stop_event.is_set():
        sys.stdout.write(f'\r{message} {next(spinner)}')
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\r' + ' ' * (len(message) + 2) + '\r')

# Simple pause animation with dots
def pause_with_dots(seconds=3):
    for i in range(seconds):
        sys.stdout.write(f"\rContinuing{'.' * (i % 4)}")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write('\r' + ' ' * 20 + '\r')

def fetch_initial_data():
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=start_spinner, args=("Fetching character and addon data from https://dbd.tricky.lol", stop_event))
    spinner_thread.start()

    try:
        characters = {
            "killer": requests.get("https://dbd.tricky.lol/api/characters?role=killer").json(),
            "survivor": requests.get("https://dbd.tricky.lol/api/characters?role=survivor").json()
        }
        killer_addons = requests.get("https://dbd.tricky.lol/api/addons?role=killer").json()
    finally:
        stop_event.set()
        spinner_thread.join()

    print("✅ Data fetched successfully.\n")
    return characters, killer_addons

def get_random_character(characters, role, checked_killers=None):
    data = characters.get(role, {})
    if not data:
        print("No characters found.")
        return None

    if role == "killer" and isinstance(data, dict):
        if checked_killers is None:
            checked_killers = set()
        available = [id for id in data.keys() if id not in checked_killers]
        if not available:
            return None, None
        character_id = random.choice(available)
        return data[character_id], character_id
    elif role == "survivor" and isinstance(data, list):
        return random.choice(data), None

def get_killer_addons(killer_item, all_addons):
    matching = [
        addon for addon in all_addons.values()
        if killer_item in addon.get("parents", []) and addon.get("type") == "poweraddon"
    ]
    return random.sample(matching, min(2, len(matching)))

def display_character(character, role, all_addons=None):
    print(f"\n🎮 Random {role.title()} Selected 🎮")
    
    # Color the killer name in blue and survivor name in green
    if role == "killer":
        print(f"{Fore.CYAN}Name: {Style.BRIGHT}{character['name']}")
    else:
        print(f"{Fore.GREEN}Name: {Style.BRIGHT}{character['name']}")
    
    print(f"ID: {character['id']}")

    if role == "killer" and all_addons:
        killer_item = character.get("item")
        if killer_item:
            addons = get_killer_addons(killer_item, all_addons)
            if addons:
                print("\n🔧 Add-ons:")
                for addon in addons:
                    # Color addon rarity (use color codes for rarities)
                    rarity_color = {
                        "common": Fore.WHITE,
                        "uncommon": Fore.YELLOW,
                        "rare": Fore.GREEN,
                        "veryrare": Fore.MAGENTA,
                        "ultrarare": Fore.RED
                    }
                    rarity = addon.get('rarity', 'common').lower()
                    print(f"{rarity_color.get(rarity, Fore.WHITE)}- {addon['name']} ({Style.BRIGHT}{addon['rarity'].title()})")
            else:
                print("No matching add-ons found.")
        else:
            print("This killer has no item reference for add-ons.")

def normalize_input(prompt, mapping):
    while True:
        user_input = input(prompt).strip().lower()
        for key, values in mapping.items():
            if user_input in values:
                return key
        print("Invalid input. Try again.")

def load_checked_killers():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return set(map(str, json.load(f)))
    return set()

def save_checked_killers(checked_killers):
    with open(SAVE_FILE, "w") as f:
        json.dump(list(checked_killers), f)

def delete_save_file():
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)

def main():
    characters, killer_addons = fetch_initial_data()

    startup_map = {
        "killer": ["killer", "k"],
        "survivor": ["survivor", "s"],
        "load": ["load", "l"]
    }
    result_map = {
        "win": ["win", "w"],
        "lose": ["lose", "l"]
    }
    decision_map = {
        "restart": ["restart", "r"],
        "quit": ["quit", "q"]
    }

    role = normalize_input("Choose a role for a new game or load a previous save (killer/survivor/load): ", startup_map)

    checked_killers = set()
    if role == "load":
        checked_killers = load_checked_killers()
        print(f"🔁 Loaded save: {len(checked_killers)} killer(s) already checked.")
        role = "killer"

    while True:
        character, character_key = get_random_character(characters, role, checked_killers)
        if not character:
            print("\n✅ All killers have been used! Game finished.")
            break

        display_character(character, role, killer_addons)

        result = normalize_input("\nDid you win or lose? (win or lose): ", result_map)

        if result == "win" and role == "killer":
            print("\n🎉 Great! You get a new random character!")
            checked_killers.add(character_key)
            save_checked_killers(checked_killers)
            pause_with_dots()
            continue
        elif result == "win":
            print("\n🎉 Great! You get a new random character!")
            pause_with_dots()
            continue
        else:
            delete_save_file()
            print("\n❌ You lost! All characters have been reset.")
            decision = normalize_input("Do you wish to restart or quit? (restart or quit): ", decision_map)
            if decision == "restart":
                print("\n🔁 Restarting with a new character...")
                pause_with_dots()
                continue
            else:
                print("\nGoodbye")
                break

if __name__ == "__main__":
    main()
