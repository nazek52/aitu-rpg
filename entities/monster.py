import math
import heapq
import random
import pygame

from settings import MONSTER_SPEED, GRID_SIZE, MONSTER_REPATH_TIME


class Monster:
    def __init__(self, x, y, size):
        w, h = size if isinstance(size, tuple) else (size, size)

        self.rect = pygame.Rect(x, y, w, h)
        self.spawn_pos = pygame.Vector2(x, y)

        self.active = False
        self.state = "idle"
        self.facing = pygame.Vector2(0, 1)

        self.vision_range = 520
        self.hearing_range = 340
        self.catch_padding = 28

        self.chase_speed = MONSTER_SPEED * 1.55
        self.search_speed = MONSTER_SPEED * 1.05
        self.patrol_speed = MONSTER_SPEED * 0.75

        self.target_pos = None
        self.last_player_pos = None

        self.path = []
        self.path_timer = 0.35
        self.search_timer = 0
        self.lost_player_timer = 0
        self.force_leave_timer = 0
        self.roam_timer = 0

        self.patrol_points = [
            (350, 260), (575, 260), (760, 260), (965, 260), (1200, 260),
            (350, 430), (760, 430), (965, 430), (1280, 430),
            (350, 620), (575, 620), (760, 620), (965, 620), (1280, 620),
            (350, 830), (575, 830), (760, 830), (965, 830), (1280, 830),
            (520, 930), (760, 930), (1050, 930), (1350, 930),
        ]
        self.patrol_index = 0

        self.anim_index = 0
        self.anim_timer = 0

    def activate(self):
        self.active = True
        self.state = "patrol"
        self.target_pos = self.patrol_points[0]
        self.path_timer = 0

    def get_hitbox(self):
        return self.rect.inflate(-self.catch_padding, -self.catch_padding)

    def distance_to_player(self, player):
        return math.hypot(
            player.rect.centerx - self.rect.centerx,
            player.rect.centery - self.rect.centery
        )

    def can_see_player(self, player, is_wall_pixel):
        if player.hidden:
            return False

        dist = self.distance_to_player(player)
        if dist > self.vision_range:
            return False

        mx, my = self.rect.center
        px, py = player.rect.center

        steps = max(12, int(dist / 10))

        for i in range(1, steps + 1):
            t = i / steps
            x = mx + (px - mx) * t
            y = my + (py - my) * t

            if is_wall_pixel(x, y):
                return False

        return True

    def can_hear_player(self, player):
        if player.hidden:
            return False

        return self.distance_to_player(player) <= self.hearing_range

    def world_to_grid(self, pos):
        x, y = pos
        return int(x // GRID_SIZE), int(y // GRID_SIZE)

    def grid_to_world(self, cell):
        gx, gy = cell
        return (
            gx * GRID_SIZE + GRID_SIZE // 2,
            gy * GRID_SIZE + GRID_SIZE // 2
        )

    def cell_blocked(self, cell, is_wall_pixel):
        cx, cy = self.grid_to_world(cell)

        radius_x = self.rect.width // 2 - 24
        radius_y = self.rect.height // 2 - 24

        points = [
            (cx, cy),
            (cx - radius_x, cy),
            (cx + radius_x, cy),
            (cx, cy - radius_y),
            (cx, cy + radius_y),
            (cx - radius_x, cy - radius_y),
            (cx + radius_x, cy - radius_y),
            (cx - radius_x, cy + radius_y),
            (cx + radius_x, cy + radius_y),
        ]

        return any(is_wall_pixel(x, y) for x, y in points)

    def find_nearest_free_cell(self, cell, is_wall_pixel):
        if not self.cell_blocked(cell, is_wall_pixel):
            return cell

        for radius in range(1, 8):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    new_cell = (cell[0] + dx, cell[1] + dy)
                    if not self.cell_blocked(new_cell, is_wall_pixel):
                        return new_cell

        return cell

    def find_path(self, start_pos, end_pos, is_wall_pixel):
        if end_pos is None:
            return []

        start = self.find_nearest_free_cell(
            self.world_to_grid(start_pos),
            is_wall_pixel
        )
        goal = self.find_nearest_free_cell(
            self.world_to_grid(end_pos),
            is_wall_pixel
        )

        if start == goal:
            return []

        open_list = []
        heapq.heappush(open_list, (0, start))

        came_from = {}
        cost = {start: 0}

        directions = [
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
        ]

        limit = 3000

        while open_list and limit > 0:
            limit -= 1
            _, current = heapq.heappop(open_list)

            if current == goal:
                break

            for dx, dy in directions:
                next_cell = (current[0] + dx, current[1] + dy)

                if self.cell_blocked(next_cell, is_wall_pixel):
                    continue

                # запрещаем диагональ сквозь углы
                if dx != 0 and dy != 0:
                    if self.cell_blocked((current[0] + dx, current[1]), is_wall_pixel):
                        continue
                    if self.cell_blocked((current[0], current[1] + dy), is_wall_pixel):
                        continue

                step_cost = 1.4 if dx != 0 and dy != 0 else 1
                new_cost = cost[current] + step_cost

                if next_cell not in cost or new_cost < cost[next_cell]:
                    cost[next_cell] = new_cost

                    heuristic = math.hypot(
                        goal[0] - next_cell[0],
                        goal[1] - next_cell[1]
                    )

                    heapq.heappush(open_list, (new_cost + heuristic, next_cell))
                    came_from[next_cell] = current

        if goal not in came_from:
            return []

        path = []
        current = goal

        while current != start:
            path.append(self.grid_to_world(current))
            current = came_from[current]

        path.reverse()
        return path

    def choose_patrol_target(self):
        import random

        possible = self.patrol_points[:]
        random.shuffle(possible)

        for point in possible:
            if point != self.target_pos:
                self.target_pos = point
                self.path = []
                self.path_timer = 0
                return

    def leave_hiding_spot(self):
        self.state = "patrol"
        self.last_player_pos = None
        self.path = []
        self.path_timer = 0
        self.force_leave_timer = 2.5

        self.target_pos = (1240, 260)

    def random_free_target(self, is_wall_pixel, attempts=80):
        import random

        for _ in range(attempts):
            x = random.randint(80, 1450)
            y = random.randint(80, 950)

            cell = self.world_to_grid((x, y))

            if not self.cell_blocked(cell, is_wall_pixel):
                return self.grid_to_world(cell)

        return self.rect.center

    def choose_roam_target(self, is_wall_pixel):
        self.target_pos = self.random_free_target(is_wall_pixel)
        self.path = []
        self.path_timer = 0
        self.roam_timer = 0

    def update_ai(self, dt, player, is_wall_pixel):
        if self.force_leave_timer > 0:
            self.force_leave_timer -= dt
            return

        if player.hidden:
            self.state = "patrol"
            self.last_player_pos = None

            self.roam_timer -= dt

            need_new_target = False

            if self.target_pos is None:
                need_new_target = True

            elif self.roam_timer <= 0:
                need_new_target = True

            else:
                dist_to_target = math.hypot(
                    self.rect.centerx - self.target_pos[0],
                    self.rect.centery - self.target_pos[1]
                )

                if dist_to_target < 45:
                    need_new_target = True

            if need_new_target:
                self.choose_roam_target(is_wall_pixel)
                self.roam_timer = 2.0

            return

        sees_player = self.can_see_player(player, is_wall_pixel)
        hears_player = self.can_hear_player(player)

        if sees_player:
            self.state = "chase"
            self.target_pos = player.rect.center
            self.last_player_pos = player.rect.center
            self.lost_player_timer = 2.2
            return

        if hears_player and self.state != "chase":
            self.state = "search"
            self.target_pos = player.rect.center
            self.last_player_pos = player.rect.center
            self.search_timer = random.uniform(5.0, 9.0)
            return

        if self.state == "chase":
            self.lost_player_timer -= dt

            if self.lost_player_timer > 0 and self.last_player_pos:
                self.target_pos = self.last_player_pos
                return

            self.state = "search"
            self.search_timer = 4.5
            self.target_pos = self.last_player_pos
            return

        if self.state == "search":
            self.search_timer -= dt

            if self.search_timer > 0 and self.last_player_pos:
                self.target_pos = self.last_player_pos
                return

            self.last_player_pos = None
            self.state = "patrol"
            self.choose_patrol_target()
            return

        if self.state == "patrol":
            if self.target_pos is None:
                self.choose_patrol_target()

            if self.target_pos:
                d = math.hypot(
                    self.rect.centerx - self.target_pos[0],
                    self.rect.centery - self.target_pos[1]
                )
                if d < 35:
                    self.choose_patrol_target()

    def forget_player_and_leave(self):
        self.state = "patrol"
        self.last_player_pos = None
        self.path = []
        self.path_timer = 0

        self.choose_patrol_target()

    def get_move_hitbox(self, rect=None):
        if rect is None:
            rect = self.rect

        return pygame.Rect(
            rect.x + rect.width * 0.25,
            rect.y + rect.height * 0.55,
            rect.width * 0.50,
            rect.height * 0.35
        )

    def move_axis(self, dx, dy, rect_hits_wall):
        moved = False

        if dx != 0:
            test = self.rect.copy()
            test.x += int(round(dx))

            if not rect_hits_wall(self.get_move_hitbox(test)):
                self.rect.x = test.x
                moved = True

        if dy != 0:
            test = self.rect.copy()
            test.y += int(round(dy))

            if not rect_hits_wall(self.get_move_hitbox(test)):
                self.rect.y = test.y
                moved = True

        return moved

    def update(self, dt, player, is_wall_pixel, rect_hits_wall):
        if not self.active:
            return

        self.update_ai(dt, player, is_wall_pixel)

        self.path_timer -= dt

        if self.path_timer <= 0:
            if self.state == "chase":
                self.path_timer = 0.18
            elif self.state == "search":
                self.path_timer = MONSTER_REPATH_TIME
            else:
                self.path_timer = 0.7

            self.path = self.find_path(
                self.rect.center,
                self.target_pos,
                is_wall_pixel
            )

        if self.path:
            target = pygame.Vector2(self.path[0])
        elif self.target_pos:
            target = pygame.Vector2(self.target_pos)
        else:
            return

        pos = pygame.Vector2(self.rect.center)
        direction = target - pos

        if direction.length() < 25:
            if self.path:
                self.path.pop(0)
            return

        if direction.length_squared() > 0:
            direction = direction.normalize()

        self.facing = direction

        if self.state == "chase":
            speed = self.chase_speed
        elif self.state == "search":
            speed = self.search_speed
        else:
            speed = self.patrol_speed

        moved = self.move_axis(
            direction.x * speed * dt,
            direction.y * speed * dt,
            rect_hits_wall
        )

        if not moved:
            self.path = []
            self.path_timer = 0

            if self.state == "chase" and self.last_player_pos:
                self.target_pos = self.last_player_pos
            else:
                self.choose_roam_target(is_wall_pixel)

        if moved:
            self.anim_timer += dt
            if self.anim_timer >= 0.10:
                self.anim_timer = 0
                self.anim_index += 1
        else:
            self.anim_index = 0

    def get_draw_image(self, image):
        if isinstance(image, dict):
            if self.state == "chase" and "chase" in image:
                frames = image["chase"]
                return frames[self.anim_index % len(frames)]

            direction = "down"

            if abs(self.facing.x) > abs(self.facing.y):
                direction = "right" if self.facing.x > 0 else "left"
            else:
                direction = "down" if self.facing.y > 0 else "up"

            frames = image.get(direction)

            if frames:
                return frames[self.anim_index % len(frames)]

        if isinstance(image, pygame.Surface):
            return image

        return None

    def draw(self, surface, cam_x, cam_y, image):
        x = self.rect.x - cam_x
        y = self.rect.y - cam_y

        img = self.get_draw_image(image)

        if img:
            surface.blit(img, (x, y))
        else:
            pygame.draw.rect(surface, (120, 0, 0), (x, y, self.rect.w, self.rect.h))