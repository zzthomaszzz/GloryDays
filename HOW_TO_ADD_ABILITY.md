# How to Add a New Ability

This is a recipe for Claude (or anyone) to add a brand-new ability to GloryDay.
Every step is required; none are optional.

---

## 1. Add stats to `ABILITY_STATS` in `server/abilities.py`

Open the file. At the very top is `ABILITY_STATS`. Add a new entry:

```python
'MyAbility': dict(
    cooldown=12.0, mana_cost=60, some_range=200, some_damage=80,
),
```

**All tunable numbers go here.** Never hardcode a number inside the class body.

---

## 2. Write the class in `server/abilities.py`

Add the class at the bottom of the file (above nothing — just append).

```python
#-------------------------------------------------------------------MyAbility
class MyAbility(AbilityBase):
    _s          = ABILITY_STATS['MyAbility']
    cooldown    = _s['cooldown']
    mana_cost   = _s['mana_cost']
    some_range  = _s['some_range']
    some_damage = _s['some_damage']

    def use(self, player, targets=None, target_pos=None, game_state=None):
        if not self.can_use(player):
            return False
        # ... validate targets / target_pos ...
        player.mana        -= self.mana_cost
        self.is_on_cooldown = True
        self.cooldown_timer = self.cooldown
        # ... do the thing ...
        return True

    def to_dict(self):
        d = super().to_dict()
        # add any keys the client needs to render visuals
        return d
```

### Circular import rule — CRITICAL

`entities.py` imports `abilities.py` at module level, which means `abilities.py`
**cannot** import `entities`, `projectiles`, or `game_state` at the top of the file.
Always defer those imports inside the method that needs them:

```python
def use(self, player, targets=None, target_pos=None, game_state=None):
    from server.projectiles import apply_damage   # avoids circular import
    from server.entities import Trap              # avoids circular import
    ...
```

### Targeting modes

The client reads `to_dict()` to decide how to draw the targeting UI:

| Flag in `to_dict()`      | Client behaviour                                   |
|--------------------------|----------------------------------------------------|
| `is_placement: True`     | Click anywhere on the map; sends `target_pos`      |
| `is_targeted: True`      | Click an enemy player; sends `targets=[pid]`       |
| `is_ally_targeted: True` | Click an ally player; sends `targets=[pid]`        |
| `is_passive: True`       | No activation — client shows it greyed out         |
| *(none of the above)*    | Instant cast with no targeting                     |

Also expose `place_range` or `cast_range` in `to_dict()` so the client draws
the correct range circle.

### Common patterns

**Channelled ability** (`is_channeling` + `channel_timer`):
```python
def __init__(self):
    super().__init__()
    self.is_channeling = False
    self.channel_timer = 0.0

def use(self, ...):
    ...
    self.is_channeling = True
    self.channel_timer = self.channel_time
    return True

def tick(self, dt, player, game_state):
    if not self.is_channeling:
        return
    self.channel_timer -= dt
    if self.channel_timer <= 0:
        self.is_channeling = False
        self._fire(player, game_state)

def to_dict(self):
    d = super().to_dict()
    d["is_channeling"] = self.is_channeling
    d["channel_timer"] = round(self.channel_timer, 2)
    d["channel_time"]  = self.channel_time
    return d
```

**Timed buff** (`is_active` + `duration_timer`):
```python
def __init__(self):
    super().__init__()
    self.is_active      = False
    self.duration_timer = 0.0

def tick(self, dt, player, game_state):
    if not self.is_active:
        return
    self.duration_timer -= dt
    if self.duration_timer <= 0:
        self.is_active = False
        # undo the buff here

def to_dict(self):
    d = super().to_dict()
    d["is_active"]      = self.is_active
    d["duration_timer"] = round(self.duration_timer, 2)
    d["duration"]       = self.duration
    return d
```

**Spawn a standard projectile** (homing, uses `Projectile`):
```python
from server.projectiles import Projectile  # avoids circular import
pid = game_state._proj_counter[0]
game_state._proj_counter[0] += 1
game_state.projectiles[pid] = Projectile(
    proj_id=pid, owner_id=player.id, owner_team=player.team,
    x=player.x, y=player.y,
    target_type="player", target_id=target_id,
    damage=self.damage, armor=0, speed=400,
)
```

**Spawn a linear projectile** (non-homing, uses `BoltProjectile`):
```python
from server.projectiles import BoltProjectile  # avoids circular import
bid = game_state._proj_counter[0]
game_state._proj_counter[0] += 1
game_state.bolt_projectiles[bid] = BoltProjectile(
    proj_id=bid, owner_id=player.id, owner_team=player.team,
    x=player.x, y=player.y, dx=dx, dy=dy,
    damage=self.damage, speed=self.speed,
)
```

**Deal melee/AoE damage immediately** (no projectile):
```python
from server.projectiles import apply_damage  # avoids circular import
apply_damage(target, self.damage, target.armor, killer=player)
```

**Apply a status effect** — set on the target player directly:
```python
target.stun_timer  = 1.5      # stuns for 1.5 s
target.slow_timer  = 2.0      # slows for 2.0 s
target.slow_factor = 0.5      # 50 % of normal speed while slowed
target.root_timer  = 1.0      # roots (can't move) for 1.0 s
```

---

## 3. Register it on a hero in `server/entities.py`

Add the class to the import block at the top:
```python
from server.abilities import (
    ...,
    MyAbility,   # ← add here
)
```

Then add it to a hero's `abilities` list inside `HERO_STATS`:
```python
HERO_STATS = {
    'Soldier': dict(
        ...
        abilities=[Snipe, MyAbility, Dash, Recall],
    ),
    ...
}
```

Slots map to keys: `[Q, E, R, B]`. Abilities are hero-independent — the same
ability class can be on multiple heroes.

---

## 4. Update the hero card description in `client/scene.py`

Search for `_HERO_CARDS`. Find the hero you added the ability to and update the
`"abilities"` list inside its card dict so the lobby shows the correct description:

```python
{
    "name": "Soldier",
    ...
    "abilities": [
        ("Q", "My Ability", "Short description"),
        ...
    ],
},
```

---

## 5. Add client-side visuals (optional but expected)

If the ability has a visible ongoing state, add rendering to `client/scene.py`
in the per-player drawing loop (search for `#Spin aura` to find the right spot).

```python
# MyAbility active ring
my_ab = next((ab for ab in abilities
              if ab and ab.get("name") == "MyAbility" and ab.get("is_active")), None)
if my_ab:
    pygame.draw.circle(screen, (200, 100, 50), (sx, sy), 22, 2)
```

The loop has access to `(sx, sy)` (screen-space position of the player) and the
full `abilities` list from the snapshot.

---

## 6. New entity types (only if needed)

If the ability places something persistent in the world (not a projectile), you need:

1. A new class in `server/entities.py` (copy `Trap` or `Banner` as a template)
2. A new `dict` and counter on `GameState` in `server/game_state.py`
3. An update/cleanup call in `GameState.update()` in `server/game_state.py`
4. Serialisation in `shared/protocol.py` (`make_snapshot`)
5. Rendering in `client/scene.py`

Only do this if you genuinely need a new entity type — most abilities can use the
existing `Projectile`, `BoltProjectile`, `apply_damage`, or status timers.

---

## Quick checklist

- [ ] Entry in `ABILITY_STATS` dict (all numbers there, none in class body)
- [ ] Class in `server/abilities.py` inheriting `AbilityBase`
- [ ] All cross-module imports deferred inside methods (`# avoids circular import`)
- [ ] `to_dict()` returns every key the client needs
- [ ] Imported and added to a hero's `default_abilities` in `server/entities.py`
- [ ] Hero card description updated in `client/scene.py`
- [ ] Client-side visual added to `client/scene.py` if ability has a visible state
