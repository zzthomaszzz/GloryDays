from shared.constants import (
    BASE_VISION, BUILDING_SIZE,
    MINERAL_START, CAPTURE_MINERAL_START, MINERALS_PER_TICK, GOLD_PER_MINERAL, GOLD_TICK_INTERVAL,
    CAPTURE_TIME, CAPTURE_RADIUS, CAPTURE_SIZE, CAPTURE_VISION, CAPTURE_HP,
)


#-------------------------------------------------------------------------------------------------------------------ShopBuilding
class ShopBuilding:
    SIZE  = 32
    RANGE = 120   # proximity radius for purchasing

    def __init__(self, shop_id, x, y):
        self.shop_id = shop_id
        self.x       = x
        self.y       = y

    def to_dict(self):
        return {
            "type":    "ShopBuilding",
            "x":       self.x,
            "y":       self.y,
            "size":    self.SIZE,
            "range":   self.RANGE,
            "is_shop": True,
        }


class BuildingBase:
    def __init__(self, size, x, y, vision, hp, armor=0):
        self.size   = size
        self.x      = x
        self.y      = y
        self.vision = vision
        self.hp     = hp
        self.max_hp = hp
        self.armor  = armor
        self.is_destroyed = False

    def update(self, dt, players): pass

    def to_dict(self):
        return {
            "type":         self.__class__.__name__,
            "x":            self.x,
            "y":            self.y,
            "size":         self.size,
            "vision":       self.vision,
            "hp":           self.hp,
            "max_hp":       self.max_hp,
            "armor":        self.armor,
            "is_destroyed": self.is_destroyed,
        }


#-------------------------------------------------------------------------------------------------------------------HQ
class BuildingHeadquarter(BuildingBase):
    def __init__(self, team, x, y):
        super().__init__(BUILDING_SIZE, x, y, BASE_VISION, hp=1000, armor=30)
        self.team         = team
        self.mineral_pool = MINERAL_START
        self._gold_timer  = 0.0

    def update(self, dt, players):
        if self.is_destroyed or self.mineral_pool <= 0:
            return
        self._gold_timer += dt
        if self._gold_timer >= GOLD_TICK_INTERVAL:
            self._gold_timer = 0.0
            self.mineral_pool = max(0, self.mineral_pool - MINERALS_PER_TICK)
            for player in players.values():
                if player.team == self.team:
                    player.gold += GOLD_PER_MINERAL

    def to_dict(self):
        d = super().to_dict()
        d["team"]         = self.team
        d["mineral_pool"] = self.mineral_pool
        return d


#-------------------------------------------------------------------------------------------------------------------CapturePoint
class CapturePoint(BuildingBase):
    def __init__(self, bid, x, y):
        super().__init__(CAPTURE_SIZE, x, y, CAPTURE_VISION, hp=CAPTURE_HP, armor=20)
        self.bid            = bid
        self.team           = 0        # 0 = neutral
        self.capture_timer  = 0.0
        self.capturing_team = None
        self._gold_timer    = 0.0
        self._mineral_pool  = CAPTURE_MINERAL_START

    def _reset(self):
        self.team           = 0
        self.hp             = self.max_hp
        self.capture_timer  = 0.0
        self.capturing_team = None
        self._gold_timer    = 0.0
        self.is_destroyed   = False

    def update(self, dt, players):
        if self.is_destroyed:
            if self._mineral_pool > 0:
                self._reset()   # minerals remain — point respawns and can be recaptured
            return              # no minerals — stays permanently destroyed

        cx = self.x + self.size // 2
        cy = self.y + self.size // 2
        r2 = CAPTURE_RADIUS * CAPTURE_RADIUS

        teams_present = set()
        for player in players.values():
            if player.is_dead:
                continue
            dx = player.x - cx
            dy = player.y - cy
            if dx * dx + dy * dy <= r2:
                teams_present.add(player.team)

        if len(teams_present) == 1:
            contesting = next(iter(teams_present))
            if contesting != self.team:
                if self.capturing_team != contesting:
                    self.capturing_team = contesting
                    self.capture_timer  = 0.0
                self.capture_timer += dt
                if self.capture_timer >= CAPTURE_TIME:
                    self.team           = contesting
                    self.capture_timer  = 0.0
                    self.capturing_team = None
        else:
            self.capture_timer  = 0.0
            self.capturing_team = None

        if self.team != 0 and self._mineral_pool > 0:
            self._gold_timer += dt
            if self._gold_timer >= GOLD_TICK_INTERVAL:
                self._gold_timer = 0.0
                self._mineral_pool = max(0, self._mineral_pool - MINERALS_PER_TICK)
                for player in players.values():
                    if player.team == self.team:
                        player.gold += GOLD_PER_MINERAL

    def to_dict(self):
        d = super().to_dict()
        d["team"]           = self.team
        d["capture_timer"]  = round(self.capture_timer, 2)
        d["capture_time"]   = CAPTURE_TIME
        d["capturing_team"] = self.capturing_team
        return d
