# Projectile classes and shared damage helpers (apply_damage, apply_on_hit_effects)
import math
import random
import time

from shared.constants import RESPAWN_TIME, KILL_GOLD

_ASSIST_WINDOW = 10.0  # seconds a damage contribution counts toward an assist
from server.abilities import ABILITY_STATS


class Projectile:
    def __init__(self, proj_id, owner_id, owner_team, x, y, target_type, target_id, damage, armor, speed):
        self.proj_id     = proj_id
        self.owner_id    = owner_id
        self.owner_team  = owner_team
        self.x           = float(x)
        self.y           = float(y)
        self.target_type = target_type
        self.target_id   = int(target_id)
        self.damage      = damage
        self.armor       = armor
        self.speed       = speed
        self.is_done     = False

    def update(self, dt, players, buildings, player_turrets=None, banners=None, traps=None):
        target = _resolve_target(self.target_type, self.target_id, players, buildings, player_turrets or {}, banners or {}, traps or {})
        if not target or getattr(target, "is_dead", False) or getattr(target, "is_destroyed", False):
            self.is_done = True
            return

        tx = getattr(target, 'cx', target.x)
        ty = getattr(target, 'cy', target.y)
        dx, dy = tx - self.x, ty - self.y
        dist   = math.sqrt(dx * dx + dy * dy)
        step   = self.speed * dt

        if dist <= step:
            killer = players.get(self.owner_id)
            apply_damage(target, self.damage, self.armor, killer=killer)
            if killer:
                apply_on_hit_effects(killer, target)
            _notify_auto_hit(target)
            self.is_done = True
        else:
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step

    def to_dict(self):
        return {
            "x":          round(self.x, 1),
            "y":          round(self.y, 1),
            "owner_team": self.owner_team,
        }


class FireballProjectile:
    def __init__(self, proj_id, owner_team, x, y, target_x, target_y,
                 tick_damage=20, ba_size=64, ba_duration=4.0, ba_tick_interval=0.5, speed=350):
        self.proj_id          = proj_id
        self.owner_team       = owner_team
        self.x                = float(x)
        self.y                = float(y)
        self.target_x         = float(target_x)
        self.target_y         = float(target_y)
        self.tick_damage      = tick_damage
        self.ba_size          = ba_size
        self.ba_duration      = ba_duration
        self.ba_tick_interval = ba_tick_interval
        self.speed            = speed
        self.is_done          = False

    def update(self, dt, burning_areas, ba_counter):
        dx   = self.target_x - self.x
        dy   = self.target_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        step = self.speed * dt
        if dist <= step:
            self.is_done = True
            from server.entities import BurningArea  # avoids circular import
            ba_id = ba_counter[0]
            ba_counter[0] += 1
            burning_areas[ba_id] = BurningArea(
                ba_id, self.target_x, self.target_y, self.owner_team,
                tick_damage=self.tick_damage,
                size=self.ba_size,
                duration=self.ba_duration,
                tick_interval=self.ba_tick_interval,
            )
        else:
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step

    def to_dict(self):
        return {
            "x":          round(self.x, 1),
            "y":          round(self.y, 1),
            "owner_team": self.owner_team,
            "is_fireball": True,
        }


class BoltProjectile:
    def __init__(self, proj_id, owner_id, owner_team, x, y, dx, dy, damage, speed):
        dist         = math.sqrt(dx * dx + dy * dy)
        self.proj_id     = proj_id
        self.owner_id    = owner_id
        self.owner_team  = owner_team
        self.x           = float(x)
        self.y           = float(y)
        self.vx          = (dx / dist) * speed
        self.vy          = (dy / dist) * speed
        self.damage      = damage
        self.angle       = math.degrees(math.atan2(-dy, dx))
        self.is_done     = False

    def update(self, dt, players):
        if self.is_done:
            return
        import pygame  # map_data imports pygame; deferred to keep server startup lean
        from shared.map_data import OBSTACLES
        nx = self.x + self.vx * dt
        ny = self.y + self.vy * dt
        hit_box = pygame.Rect(int(nx - 4), int(ny - 4), 8, 8)
        if any(obs.colliderect(hit_box) for obs in OBSTACLES):
            self.is_done = True
            return
        self.x, self.y = nx, ny
        for p in players.values():
            if p.is_dead or p.team == self.owner_team:
                continue
            ddx = p.x - self.x
            ddy = p.y - self.y
            if ddx * ddx + ddy * ddy <= (p.size + 5) ** 2:
                apply_damage(p, self.damage, p.armor)
                self.is_done = True
                return

    def to_dict(self):
        return {
            "x":          round(self.x, 1),
            "y":          round(self.y, 1),
            "owner_team": self.owner_team,
            "angle":      round(self.angle, 1),
            "is_bolt":    True,
        }


class HookProjectile:
    _s         = ABILITY_STATS['Hook']
    SPEED      = _s['speed']
    MAX_RANGE  = _s['max_range']
    HIT_RADIUS = _s['hit_radius']
    PULL_DIST  = _s['pull_dist']
    PULL_DUR   = _s['pull_dur']
    DAMAGE     = _s['damage']
    AD_RATIO   = _s['ad_ratio']
    STUN_DUR   = _s['stun_dur']

    def __init__(self, proj_id, owner_id, owner_team, x, y, dx, dy):
        dist            = math.sqrt(dx * dx + dy * dy) or 1
        self.proj_id    = proj_id
        self.owner_id   = owner_id
        self.owner_team = owner_team
        self.x          = float(x)
        self.y          = float(y)
        self.vx         = (dx / dist) * self.SPEED
        self.vy         = (dy / dist) * self.SPEED
        self.traveled   = 0.0
        self.is_done    = False

    def update(self, dt, players):
        if self.is_done:
            return
        self.x         += self.vx * dt
        self.y         += self.vy * dt
        self.traveled  += self.SPEED * dt
        if self.traveled >= self.MAX_RANGE:
            self.is_done = True
            return
        for p in players.values():
            if p.is_dead or p.team == self.owner_team:
                continue
            ddx = p.x - self.x
            ddy = p.y - self.y
            if ddx * ddx + ddy * ddy <= self.HIT_RADIUS ** 2:
                self._apply_hook(p, players)
                self.is_done = True
                return

    def _apply_hook(self, target, players):
        owner = players.get(self.owner_id)
        damage = self.DAMAGE + int(getattr(owner, 'attack_damage', 0) * self.AD_RATIO)
        apply_damage(target, damage, target.armor, killer=owner)
        target.stun_timer = max(getattr(target, 'stun_timer', 0), self.STUN_DUR)
        if not owner or owner.is_dead:
            return
        dx   = owner.x - target.x
        dy   = owner.y - target.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist <= self.PULL_DIST:
            return
        # Velocity-based pull — target flies through the air over PULL_DUR seconds
        travel      = dist - self.PULL_DIST
        nx, ny      = dx / dist, dy / dist
        target.pull_vx    = nx * travel / self.PULL_DUR
        target.pull_vy    = ny * travel / self.PULL_DUR
        target.pull_timer = self.PULL_DUR

    def to_dict(self):
        return {
            "x":          round(self.x, 1),
            "y":          round(self.y, 1),
            "owner_id":   self.owner_id,
            "owner_team": self.owner_team,
        }


class NetProjectile:
    _LAND_LINGER = 0.4   # seconds the landed net stays visible before despawning

    def __init__(self, proj_id, owner_id, owner_team, x, y, tx, ty, net_radius, root_dur, speed):
        self.proj_id    = proj_id
        self.owner_id   = owner_id
        self.owner_team = owner_team
        self.x          = float(x)
        self.y          = float(y)
        self.tx         = float(tx)
        self.ty         = float(ty)
        self.net_radius = net_radius
        self.root_dur   = root_dur
        self.speed      = speed
        self.is_landed  = False
        self._land_timer = 0.0
        self.is_done    = False

    def update(self, dt, players, buildings, player_turrets=None, banners=None, traps=None):
        if self.is_landed:
            self._land_timer -= dt
            if self._land_timer <= 0:
                self.is_done = True
            return
        dx, dy = self.tx - self.x, self.ty - self.y
        dist   = math.sqrt(dx * dx + dy * dy)
        step   = self.speed * dt
        if dist <= step:
            self.x, self.y  = self.tx, self.ty
            self.is_landed  = True
            self._land_timer = self._LAND_LINGER
            self._apply_root(players)
        else:
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step

    def _apply_root(self, players):
        r2 = self.net_radius ** 2
        for p in players.values():
            if p.is_dead or p.team == self.owner_team:
                continue
            dx = p.x - self.x
            dy = p.y - self.y
            if dx * dx + dy * dy <= r2:
                p.root_timer = max(p.root_timer, self.root_dur)

    def to_dict(self):
        return {
            "x":          round(self.x, 1),
            "y":          round(self.y, 1),
            "owner_team": self.owner_team,
            "is_net":     True,
            "is_landed":  self.is_landed,
            "radius":     self.net_radius,
        }


class FatedMissileProjectile:
    def __init__(self, proj_id, owner_id, owner_team, x, y, target_id, damage, speed, stun_dur):
        self.proj_id    = proj_id
        self.owner_id   = owner_id
        self.owner_team = owner_team
        self.x          = float(x)
        self.y          = float(y)
        self.target_id  = int(target_id)
        self.damage     = damage
        self.speed      = speed
        self.stun_dur   = stun_dur
        self.is_done    = False

    def update(self, dt, players, buildings, player_turrets=None, banners=None, traps=None):
        target = players.get(self.target_id)
        if not target or target.is_dead:
            self.is_done = True
            return
        dx, dy = target.x - self.x, target.y - self.y
        dist   = math.sqrt(dx * dx + dy * dy)
        step   = self.speed * dt
        if dist <= step:
            killer = players.get(self.owner_id)
            apply_damage(target, self.damage, 0, killer=killer)
            target.stun_timer = max(getattr(target, 'stun_timer', 0), self.stun_dur)
            self.is_done = True
        else:
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step

    def to_dict(self):
        return {
            "x":                round(self.x, 1),
            "y":                round(self.y, 1),
            "owner_team":       self.owner_team,
            "is_fated_missile": True,
        }


def _notify_auto_hit(target):
    for ab in getattr(target, 'abilities', []):
        if ab is not None and hasattr(ab, 'on_auto_hit'):
            ab.on_auto_hit(target)


def _resolve_target(target_type, target_id, players, buildings, player_turrets, banners, traps=None):
    match target_type:
        case "player":   return players.get(target_id)
        case "building": return buildings.get(target_id)
        case "turret":   return player_turrets.get(target_id)
        case "banner":   return banners.get(target_id)
        case "trap":     return (traps or {}).get(target_id)
    return None


def apply_on_hit_effects(attacker, target):
    if not hasattr(target, 'armor_reduction_timer'):
        return
    if any(item == 'Fang' for item in getattr(attacker, 'inventory', [])):
        target.armor_reduction = 10
        target.armor_reduction_timer = 3.0


_ARMOR_SCALE = 3   # tune to adjust how strongly armor reduces damage


def apply_damage(target, raw_damage, armor, killer=None):
    effective_armor = max(0, armor - getattr(target, 'armor_reduction', 0))
    is_crit = False

    if killer is not None:
        for ab in getattr(killer, 'abilities', []):
            if ab is not None and hasattr(ab, 'crit_chance'):
                if random.random() < ab.crit_chance:
                    raw_damage = int(raw_damage * ab.crit_mult)
                    is_crit = True
                break

    if getattr(target, 'is_invulnerable', False):
        return

    damage = max(1, int(raw_damage * 100 // (100 + effective_armor * _ARMOR_SCALE)))
    target.hp -= damage

    if is_crit and killer is not None:
        killer.hp = min(killer.max_hp, killer.hp + damage)

    # Log attacker for assist tracking (players only)
    if killer is not None and hasattr(target, 'damage_log') and hasattr(killer, 'id'):
        target.damage_log[killer.id] = time.monotonic()

    if target.hp <= 0:
        target.hp = 0
        if hasattr(target, "is_destroyed"):
            target.is_destroyed = True
        elif hasattr(target, "is_dead"):
            target.is_dead = True
            target.respawn_timer = RESPAWN_TIME
            if killer is not None and getattr(killer, "team", None) != getattr(target, "team", None):
                killer.gold        += KILL_GOLD
                killer.kills       += 1
                killer.kill_streak += 1
                target.deaths      += 1
                target._had_bounty       = getattr(target, 'kill_streak', 0) >= 3
                target._assist_killer_id = getattr(killer, 'id', None)  # resolved in game_state.update
