# Map renderer: draws tiles, obstacles, bushes, and fog-of-war
import pygame
import math
from collections import deque

from client.node import Node
from shared.constants import NODE_SIZE, MAP_W, MAP_H


class MapSystem:
    def __init__(self, obstacles, spawns):
        self.size = NODE_SIZE
        self.node_x = MAP_W // self.size
        self.node_y = MAP_H // self.size
        self.obstacles = obstacles
        self.spawns = spawns

        self.nodes = []
        self.discovered_nodes = []
        self.building_vision_nodes = []
        self._fog_surface = pygame.Surface((MAP_W, MAP_H), pygame.SRCALPHA)

        self._init_nodes()
        self._set_obstacles()
        self._set_spawns()

    def _init_nodes(self):
        for y in range(self.node_y):
            self.nodes.append([])
            for x in range(self.node_x):
                self.nodes[y].append(Node(x * self.size, y * self.size))

    def _set_obstacles(self):
        for row in self.nodes:
            for node in row:
                if node.rect.collidelist(self.obstacles) >= 0:
                    node.traversable = 0

    def _set_spawns(self):
        for row in self.nodes:
            for node in row:
                if node.rect.collidelist(self.spawns) >= 0:
                    node.isSpawn = 1

    def get_adjacent(self, node):
        adj = []
        x = round(node.grid_id[0])
        y = round(node.grid_id[1])
        if x > 0:               adj.append(self.nodes[y][x - 1])
        if x < self.node_x - 1: adj.append(self.nodes[y][x + 1])
        if y > 0:               adj.append(self.nodes[y - 1][x])
        if y < self.node_y - 1: adj.append(self.nodes[y + 1][x])
        return adj

    def get_node_from_pos(self, pos_x, pos_y):
        x = max(0, min(int(pos_x // self.size), self.node_x - 1))
        y = max(0, min(int(pos_y // self.size), self.node_y - 1))
        return self.nodes[y][x]

    def _run_bfs(self, origin, vision, write_building=False):
        queue = deque([origin])
        visited = {id(origin)}

        while queue:
            node = queue.popleft()

            if math.hypot(node.cx - origin.cx, node.cy - origin.cy) > vision:
                continue

            visible = True
            for obstacle in self.obstacles:
                if obstacle.clipline(node.cx, node.cy, origin.cx, origin.cy):
                    if node.traversable:
                        visible = False
                        break

            if visible:
                if write_building:
                    if not node.building_vision:
                        node.building_vision = True
                        self.building_vision_nodes.append(node)
                else:
                    if not node.discovered:
                        node.discovered = 1
                        self.discovered_nodes.append(node)

                for adj in self.get_adjacent(node):
                    if id(adj) not in visited:
                        visited.add(id(adj))
                        queue.append(adj)

    def handle_fog(self, player_sources):
        # player_sources: list of (origin_node, vision_radius)
        for node in self.discovered_nodes:
            node.discovered = 0
        self.discovered_nodes.clear()
        for origin, vision in player_sources:
            self._run_bfs(origin, vision, write_building=False)

    def compute_building_vision(self, building_sources):
        # building_sources: list of (origin_node, vision_radius)
        for node in self.building_vision_nodes:
            node.building_vision = False
        self.building_vision_nodes.clear()
        for origin, vision in building_sources:
            self._run_bfs(origin, vision, write_building=True)

    def draw(self, surface, cam_x=0, cam_y=0):
        self._fog_surface.fill((0, 0, 0, 160))
        for node in self.discovered_nodes:
            self._fog_surface.fill((0, 0, 0, 0), node.rect)
        for node in self.building_vision_nodes:
            self._fog_surface.fill((0, 0, 0, 0), node.rect)
        surface.blit(self._fog_surface, (-int(cam_x), -int(cam_y)))
