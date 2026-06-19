import asyncio
import json
import socket
import time
from shared.protocol import make_input_message, make_hero_select_message


class NetworkClient:
    def __init__(self, host, port, snapshot_interval):
        self.host = host
        self.port = port
        self.snapshot_interval = snapshot_interval

        self.reader = None
        self.writer = None

        self.latest_snapshot = {}
        self.previous_snapshot = {}
        self.last_snapshot_time = 0.0

        self.my_player_id = None
        self.my_team = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        sock = self.writer.get_extra_info('socket')
        if sock:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    async def wait_for_welcome(self, timeout=10.0):
        deadline = time.time() + timeout
        while self.my_player_id is None:
            if time.time() > deadline:
                return False
            await asyncio.sleep(0.05)
        return True

    async def receive_loop(self):
        while True:
            try:
                line = await self.reader.readline()
            except (ConnectionError, OSError):
                break

            if not line:
                break

            try:
                msg = json.loads(line.decode())
            except Exception:
                continue

            if msg.get("type") == "welcome":
                self.my_player_id = str(msg["player_id"])
                self.my_team = msg["team"]
                continue
            self.previous_snapshot = self.latest_snapshot
            self.latest_snapshot = msg
            self.last_snapshot_time = time.time()

    async def send_hero_select(self, hero_name):
        if self.writer is None or self.writer.is_closing():
            return
        payload = make_hero_select_message(hero_name)
        data = (json.dumps(payload) + "\n").encode()
        try:
            self.writer.write(data)
            await self.writer.drain()
        except (ConnectionError, OSError):
            pass

    async def send_ready(self):
        if self.writer is None or self.writer.is_closing():
            return
        data = (json.dumps({"type": "ready"}) + "\n").encode()
        try:
            self.writer.write(data)
            await self.writer.drain()
        except (ConnectionError, OSError):
            pass

    async def send_force_start(self):
        if self.writer is None or self.writer.is_closing():
            return
        data = (json.dumps({"type": "force_start"}) + "\n").encode()
        try:
            self.writer.write(data)
            await self.writer.drain()
        except (ConnectionError, OSError):
            pass

    async def send_sell_item(self, slot):
        if self.writer is None or self.writer.is_closing():
            return
        data = (json.dumps({"type": "sell_item", "slot": slot}) + "\n").encode()
        try:
            self.writer.write(data)
            await self.writer.drain()
        except (ConnectionError, OSError):
            pass

    async def send_buy_item(self, item_name):
        if self.writer is None or self.writer.is_closing():
            return
        payload = {"type": "buy_item", "item": item_name}
        data = (json.dumps(payload) + "\n").encode()
        try:
            self.writer.write(data)
            await self.writer.drain()
        except (ConnectionError, OSError):
            pass

    async def send_input(self, dx, dy, attack=None, ability=None, ability_target=None, ability_target_id=None):
        if self.writer is None or self.writer.is_closing():
            return
        payload = make_input_message(dx, dy, attack, ability, ability_target, ability_target_id)
        data = (json.dumps(payload) + "\n").encode()
        try:
            self.writer.write(data)
            await self.writer.drain()
        except (ConnectionError, OSError):
            pass

    def get_interpolated_pos(self, category, entity_id):
        latest   = self.latest_snapshot.get(category, {})
        previous = self.previous_snapshot.get(category, {})
        if entity_id not in latest:
            return None
        if entity_id not in previous:
            return latest[entity_id]["pos"]
        elapsed = time.time() - self.last_snapshot_time
        t = min(elapsed / self.snapshot_interval, 1.0)
        prev_x, prev_y = previous[entity_id]["pos"]
        curr_x, curr_y = latest[entity_id]["pos"]
        return [prev_x + (curr_x - prev_x) * t, prev_y + (curr_y - prev_y) * t]

    def get_interpolated_xy(self, category, entity_id):
        """Interpolate entities stored as {x: float, y: float} (projectiles, fireballs)."""
        latest   = self.latest_snapshot.get(category, {})
        previous = self.previous_snapshot.get(category, {})
        if entity_id not in latest:
            return None
        cur = latest[entity_id]
        if entity_id not in previous:
            return cur["x"], cur["y"]
        elapsed = time.time() - self.last_snapshot_time
        t = min(elapsed / self.snapshot_interval, 1.0)
        prv = previous[entity_id]
        return (
            prv["x"] + (cur["x"] - prv["x"]) * t,
            prv["y"] + (cur["y"] - prv["y"]) * t,
        )

    def get_entity_ids(self, category):
        return list(self.latest_snapshot.get(category, {}).keys())