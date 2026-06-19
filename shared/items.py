# ITEMS dict: all purchasable items with cost, stat deltas, and shop display text
ITEMS = {
    "Scythe": {
        "cost":   100,
        "stats":  {"attack_damage": 35, "attack_speed": 0.2},
        "label":  "SCY",
        "desc":   "+35 Attack Damage  +0.2 Atk Speed",
    },
    "Chain Vest": {
        "cost":   80,
        "stats":  {"armor": 20, "magic_resist": 20, "max_hp": 200},
        "label":  "CVS",
        "desc":   "+20 Armor  +20 Magic Resist  +200 HP",
    },
    "Staff": {
        "cost":   100,
        "stats":  {"ability_power": 65},
        "label":  "STF",
        "desc":   "+65 Ability Power",
    },
    "Ancient Rune": {
        "cost":   30,
        "stats":  {"hp_regen": 4, "mana_regen": 2},
        "label":  "RUN",
        "desc":   "+4 HP Regen / sec  +2 Mana Regen / sec",
    },
    "Boots": {
        "cost":   30,
        "stats":  {"speed": 20},
        "label":  "BOT",
        "desc":   "+20 Move Speed",
    },
    "Fang": {
        "cost":   80,
        "stats":  {"attack_damage": 25},
        "label":  "FNG",
        "desc":   "+25 Damage  -10 enemy armor on hit (3s)",
    },
    "Iron Heart": {
        "cost":   80,
        "stats":  {"max_hp": 450},
        "label":  "IHT",
        "desc":   "+450 Max HP",
    },
    "Grimoire": {
        "cost":   70,
        "stats":  {"max_mana": 100, "ability_power": 40},
        "label":  "GRM",
        "desc":   "+100 Max Mana  +40 Ability Power",
    },
    "Null Stone": {
        "cost":   70,
        "stats":  {"magic_resist": 30, "max_mana": 100},
        "label":  "NLS",
        "desc":   "+30 Magic Resist  +100 Max Mana",
    },
    "Swiftblade": {
        "cost":   70,
        "stats":  {"attack_damage": 20, "speed": 15},
        "label":  "SWB",
        "desc":   "+20 Attack Damage  +15 Move Speed",
    },
}

ITEM_KEYS = list(ITEMS.keys())
