# How to Add a New Hero

Adding a hero touches two files plus a sprite image.
The lobby card is generated automatically — no manual UI work needed.

---

## 1. Add to `shared/heroes.py`

This is the single source of truth for stats and lobby display.
Add a new entry to `HERO_STATS`:

```python
'MyHero': dict(
    # Game stats (used by the server)
    hp=500, mana=300, attack_damage=65, ability_power=0,
    attack_range=80,  attack_speed=0.8,  crit_chance=0.0,
    armor=28, magic_resist=30, speed=105, vision=170,
    is_ranged=False, proj_speed=0,

    # Lobby display (used by the client automatically)
    desc="One-line flavour description shown in the lobby.",
    ability_descs=[
        ("Q", "Ability A", "Short description"),
        ("E", "Ability B", "Short description"),
        ("R", "Ability C", "Short description"),
        # B slot (Recall) is always added automatically — don't list it
    ],
),
```

### Required keys

| Key | Type | Notes |
|-----|------|-------|
| `hp` | int | Starting and max HP |
| `mana` | int | Starting and max mana |
| `attack_damage` | int | Base auto-attack damage |
| `ability_power` | int | Scales magic abilities |
| `attack_range` | int | Pixels; <80 = melee feel, 100+ = ranged feel |
| `attack_speed` | float | Attacks per second |
| `crit_chance` | float | 0.0 – 1.0 |
| `armor` | int | Physical damage reduction |
| `magic_resist` | int | Magic damage reduction |
| `speed` | int | Movement speed in pixels/sec |
| `vision` | int | Fog-of-war reveal radius in pixels |
| `is_ranged` | bool | `True` fires a projectile; `False` = melee |
| `proj_speed` | int | Projectile pixels/sec; set `0` for melee heroes |
| `desc` | str | Lobby flavour text |
| `ability_descs` | list | `[(key, name, desc), ...]` for Q/E/R slots |

For abilities that don't exist yet, write them first following `HOW_TO_ADD_ABILITY.md`.

---

## 2. Add ability classes to `server/entities.py`

`HERO_ABILITIES` maps hero names to the actual ability classes (can't live in shared/
because they're server-only Python classes). Add your hero's loadout:

```python
HERO_ABILITIES = {
    ...
    'MyHero': [AbilityA, AbilityB, AbilityC, Recall],
}
```

Also add any new ability classes to the import block at the top of the file:
```python
from server.abilities import (
    ...,
    AbilityA, AbilityB, AbilityC,
)
```

Slots map to keys `[Q, E, R, B]`. Last slot is always `Recall`.

---

## 3. Add the sprite

Add an entry to `HERO_ASSET_MAP` in `client/scene.py`:

```python
HERO_ASSET_MAP = {
    ...
    "MyHero": os.path.join(_ROOT, "asset", "myhero.png"),
}
```

Then drop `myhero.png` in the `asset/` folder.
Recommended size: 32×32 px (same as all existing heroes).
If the file is missing the client falls back to `default_player.png` — no crash.

---

## Quick checklist

- [ ] Entry in `HERO_STATS` in `shared/heroes.py` (all 15 keys present)
- [ ] Entry in `HERO_ABILITIES` in `server/entities.py`
- [ ] New ability classes imported at the top of `server/entities.py`
- [ ] Entry in `HERO_ASSET_MAP` in `client/scene.py`
- [ ] Sprite PNG in `asset/`
- [ ] Verify: hero appears in lobby, correct stats shown, all abilities work in-game
