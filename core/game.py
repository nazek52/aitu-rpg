import math

import pygame

from entities.player import Player
from entities.monster import Monster
from objects.item import Collectible, Note

from settings import *
from utils import load_image, load_json, save_json


class Game:
    def __init__(self, screen):
        self.screen = screen
        # The animated GIF menu is handled in main.py.
        # Game.py starts directly in gameplay after ENTER.
        self.state = "play"

        pygame.mixer.init()

        self.snd_pickup = pygame.mixer.Sound("assets/sounds/pickup.wav")
        self.snd_generator = pygame.mixer.Sound("assets/sounds/generator.wav")
        self.snd_scream = pygame.mixer.Sound("assets/sounds/monster_scream.wav")
        self.snd_death = pygame.mixer.Sound("assets/sounds/death.wav")
        self.snd_monster_chase = pygame.mixer.Sound("assets/sounds/monster_chase.wav")
        self.snd_heartbeat = pygame.mixer.Sound("assets/sounds/heartbeat.wav")

        self.snd_pickup.set_volume(0.4)
        self.snd_generator.set_volume(0.8)
        self.snd_scream.set_volume(2.0)
        self.snd_monster_chase.set_volume(1.0)
        self.snd_heartbeat.set_volume(0.7)
        self.snd_death.set_volume(2.5)

        self.generator_channel = pygame.mixer.Channel(1)

        pygame.mixer.music.set_volume(0.35)

        self.font_big = pygame.font.SysFont("consolas", 72, bold=True)
        self.font_mid = pygame.font.SysFont("consolas", 34, bold=True)
        self.font = pygame.font.SysFont("consolas", 22)
        self.small_font = pygame.font.SysFont("consolas", 16)

        self.map_img = load_image("map.png", alpha=False)
        self.collision_img = load_image("collision.png", alpha=False)

        self.map_w = self.map_img.get_width()
        self.map_h = self.map_img.get_height()

        self.col_w = self.collision_img.get_width()
        self.col_h = self.collision_img.get_height()

        self.camera_zoom = ZOOM
        self.view_w = int(SCREEN_W / self.camera_zoom)
        self.view_h = int(SCREEN_H / self.camera_zoom)

        self.player_images = {
            "up": [
                load_image("up1.png", PLAYER_SIZE),
                load_image("up2.png", PLAYER_SIZE)
            ],
            "down": [
                load_image("down1.png", PLAYER_SIZE),
                load_image("down2.png", PLAYER_SIZE)
            ],
            "left": [
                load_image("left1.png", PLAYER_SIZE),
                load_image("left2.png", PLAYER_SIZE)
            ],
            "right": [
                load_image("right1.png", PLAYER_SIZE),
                load_image("right2.png", PLAYER_SIZE)
            ],
        }

        self.monster_img = {
            "up": [
                load_image("up1m.png", MONSTER_SIZE),
                load_image("up2m.png", MONSTER_SIZE),
            ],
            "down": [
                load_image("down1m.png", MONSTER_SIZE),
                load_image("down2m.png", MONSTER_SIZE),
            ],
            "right": [
                load_image("right1m.png", MONSTER_SIZE),
                load_image("right2m.png", MONSTER_SIZE),
            ],
            "left": [
                load_image("left1m.png", MONSTER_SIZE),
                load_image("left2m.png", MONSTER_SIZE),
            ],
            "chase": [
                load_image("chase1.png", MONSTER_SIZE),
                load_image("chase2.png", MONSTER_SIZE),
                load_image("chase3.png", MONSTER_SIZE),
                load_image("chase4.png", MONSTER_SIZE),
            ],
        }

        self.monster_chase_img = {
            "up": [
                load_image("upmch1.png", MONSTER_SIZE),
                load_image("upmch2.png", MONSTER_SIZE),
                load_image("upmch3.png", MONSTER_SIZE),
                load_image("upmch4.png", MONSTER_SIZE),
            ],
            "down": [
                load_image("downmch1.png", MONSTER_SIZE),
                load_image("downmch2.png", MONSTER_SIZE),
                load_image("downmch3.png", MONSTER_SIZE),
                load_image("downmch4.png", MONSTER_SIZE),
            ],
            "right": [
                load_image("rightmch1.png", MONSTER_SIZE),
                load_image("rightmch2.png", MONSTER_SIZE),
                load_image("rightmch3.png", MONSTER_SIZE),
                load_image("rightmch4.png", MONSTER_SIZE),
            ],
            "left": [
                load_image("leftmch1.png", MONSTER_SIZE),
                load_image("leftmch2.png", MONSTER_SIZE),
                load_image("leftmch3.png", MONSTER_SIZE),
                load_image("leftmch4.png", MONSTER_SIZE),
            ],
        }

        self.item_images = {
            "Fuse A": load_image("fusea.png", ITEM_SIZE),
            "Fuse B": load_image("fuseb.png", ITEM_SIZE),
            "Keycard": load_image("keycard.png", ITEM_SIZE),
            "Reagent": load_image("reagent.png", ITEM_SIZE),
            "Stabilizer": load_image("Stabilizer.png", ITEM_SIZE),
            "Tissue Sample": load_image("tissuesample.png", ITEM_SIZE),
        }

        self.note_img = load_image("notes.png", NOTE_SIZE)

        self.dead_monster_img = load_image(
            "dead_monster.png",
            DEAD_MONSTER_SIZE
        )

        scores = load_json(SCORE_FILE, {"high_score": 0, "best_time": 0})
        self.high_score = scores.get("high_score", 0)
        self.best_time = scores.get("best_time", 0)

        self.reset_world()
        self.play_game_music()

    def reset_world(self):
        self.player = Player(500, 500, PLAYER_SIZE)
        self.monster = Monster(1260, 420, MONSTER_SIZE)

        self.camera_x = 0
        self.camera_y = 0

        self.inventory = []
        self.trunk = []

        self.score = 0
        self.start_ticks = pygame.time.get_ticks()

        self.message = ""
        self.message_until = 0

        self.warning_text = ""
        self.warning_until = 0

        self.note_open = False
        self.current_note = None

        self.monster_wake_pending = False
        self.monster_wake_time = 0

        self.generator_on = False

        self.heartbeat_timer = 0

        self.monster_chase_playing = False
        self.monster_sound_timer = 0

        self.toxin_ready = False
        self.monster_dead = False
        self.player_has_toxin = False
        self.exit_open = False

        self.shake_timer = 0
        self.shake_power = 0

        self.trunk_rect = pygame.Rect(680, 760, 90, 70)
        self.generator_rect = pygame.Rect(595, 125, 130, 100)
        self.main_lab_rect = pygame.Rect(1060, 780, 110, 80)
        self.exit_rect = pygame.Rect(1375, 815, 90, 100)

        self.hiding_spots = [
            pygame.Rect(135, 760, 80, 70),
            pygame.Rect(150, 950, 80, 70),
            pygame.Rect(150, 560, 80, 70),
            pygame.Rect(1280, 90, 80, 70),
            pygame.Rect(1030, 360, 80, 70),
            pygame.Rect(935, 785, 80, 70),
            pygame.Rect(470, 390, 85, 70),
            pygame.Rect(720, 330, 85, 70),
            pygame.Rect(850, 610, 85, 70),
            pygame.Rect(1190, 645, 85, 70),
            pygame.Rect(1380, 380, 85, 70),
            pygame.Rect(360, 820, 85, 70),
            pygame.Rect(610, 980, 85, 70),

            pygame.Rect(250, 250, 85, 70),
            pygame.Rect(420, 180, 85, 70),
            pygame.Rect(680, 180, 85, 70),
            pygame.Rect(910, 250, 85, 70),
            pygame.Rect(1160, 250, 85, 70),
            pygame.Rect(1320, 520, 85, 70),
            pygame.Rect(1050, 560, 85, 70),
            pygame.Rect(740, 720, 85, 70),
            pygame.Rect(520, 670, 85, 70),
            pygame.Rect(270, 720, 85, 70),
            pygame.Rect(230, 1040, 85, 70),
            pygame.Rect(520, 1080, 85, 70),
            pygame.Rect(850, 1020, 85, 70),
            pygame.Rect(1160, 930, 85, 70),
            pygame.Rect(1430, 760, 85, 70),
        ]

        self.items = [
            Collectible("Fuse A", 190, 620, self.item_images["Fuse A"]),
            Collectible("Fuse B", 210, 390, self.item_images["Fuse B"]),
            Collectible("Keycard", 1290, 100, self.item_images["Keycard"]),
            Collectible("Reagent", 1120, 155, self.item_images["Reagent"]),
            Collectible("Stabilizer", 990, 190, self.item_images["Stabilizer"]),
            Collectible("Tissue Sample", 1100, 390, self.item_images["Tissue Sample"]),
        ]

        self.notes = [
            Note(
                "Emergency Notice",
                "Backup power is offline. Find two fuses and restore the generator.",
                505,
                430,
                self.note_img
            ),
            Note(
                "Medical Log",
                "F-13 reacts to noise and movement. Hiding may save your life.",
                210,
                945,
                self.note_img
            ),
            Note(
                "Archive Note",
                "Main Laboratory access code starts with 7.",
                310,
                105,
                self.note_img
            ),
            Note(
                "Security Report",
                "The keycard is stored in Security Office. Code segment: 4.",
                1420,
                85,
                self.note_img
            ),
            Note(
                "Chemical Draft",
                "Toxin formula requires Reagent, Stabilizer, and Tissue Sample. Final code: 2.",
                1100,
                360,
                self.note_img
            ),
        ]

    def reset(self):
        self.reset_world()
        self.state = "play"
        self.play_game_music()

    def game_time(self):
        return int((pygame.time.get_ticks() - self.start_ticks) / 1000)

    def set_message(self, text, duration=2400):
        self.message = text
        self.message_until = pygame.time.get_ticks() + duration

    def set_warning(self, text="WARNING: F-13 is near!", duration=900):
        self.warning_text = text
        self.warning_until = pygame.time.get_ticks() + duration

    def clear_warning(self):
        self.warning_text = ""
        self.warning_until = 0

    def get_objective_text(self):
        if not self.generator_on:
            if not self.has_item("Fuse A") or not self.has_item("Fuse B"):
                return "TASK: Find Fuse A + Fuse B"
            return "TASK: Go to GENERATOR and press E"
        if not self.toxin_ready:
            needed = []
            for item in ["Reagent", "Stabilizer", "Tissue Sample"]:
                if not self.has_item(item):
                    needed.append(item)
            if needed:
                return "TASK: Collect " + ", ".join(needed)
            return "TASK: Go to MAIN LAB and press E"
        if not self.exit_open:
            return "TASK: Unlock the exit"
        return "TASK: Run to EXIT and press E"

    def monster_distance(self):
        return math.hypot(
            self.player.rect.centerx - self.monster.rect.centerx,
            self.player.rect.centery - self.monster.rect.centery
        )

    def play_menu_music(self):
        pygame.mixer.music.load("assets/sounds/menu_music.mp3")
        pygame.mixer.music.set_volume(0.45)
        pygame.mixer.music.play(-1)

    def play_game_music(self):
        pygame.mixer.music.load("assets/sounds/ambient.mp3")
        pygame.mixer.music.set_volume(0.15)
        pygame.mixer.music.play(-1)

    def save_score(self):
        data = load_json(SCORE_FILE, {"high_score": 0, "best_time": 0})

        if self.score > data.get("high_score", 0):
            data["high_score"] = self.score

        if self.state == "win":
            current_time = self.game_time()
            best_time = data.get("best_time", 0)

            if best_time == 0 or current_time < best_time:
                data["best_time"] = current_time

        save_json(SCORE_FILE, data)

    def save_progress(self):
        data = {
            "inventory": self.inventory,
            "trunk": self.trunk,
            "score": self.score,
            "generator_on": self.generator_on,
            "toxin_ready": self.toxin_ready,
            "exit_open": self.exit_open
        }

        save_json(SAVE_FILE, data)

    def handle_keydown(self, key):
        if self.state in ["game_over", "win"]:
            if key == pygame.K_r:
                self.reset()
            return

        if self.state != "play":
            return

        if key == pygame.K_e:
            self.interact()

        elif key == pygame.K_h:
            self.hide()

        elif key == pygame.K_1:
            self.store_to_trunk()

        elif key == pygame.K_2:
            self.take_from_trunk()

        elif key == pygame.K_j:
            self.save_progress()
            self.set_message("Game saved.")

    def is_wall_pixel(self, x, y):
        if x < 0 or y < 0 or x >= self.map_w or y >= self.map_h:
            return True

        cx = int(x * self.col_w / self.map_w)
        cy = int(y * self.col_h / self.map_h)

        if cx < 0 or cy < 0 or cx >= self.col_w or cy >= self.col_h:
            return True

        color = self.collision_img.get_at((cx, cy))

        return (
                color.r < 50
                and color.g < 50
                and color.b < 50
        )

    def rect_hits_wall(self, rect):
        feet = pygame.Rect(
            rect.x + 8,
            rect.y + rect.height - 22,
            rect.width - 16,
            18
        )

        points = [
            feet.topleft,
            feet.topright,
            feet.bottomleft,
            feet.bottomright,
            feet.midtop,
            feet.midbottom,
            feet.midleft,
            feet.midright,
            feet.center
        ]

        for x, y in points:
            if self.is_wall_pixel(x, y):
                return True

        return False

    def move_player(self, dx, dy):
        if self.player.hidden:
            return

        new_rect = self.player.rect.copy()
        new_rect.x += int(dx)

        if not self.rect_hits_wall(new_rect):
            self.player.rect.x = new_rect.x

        new_rect = self.player.rect.copy()
        new_rect.y += int(dy)

        if not self.rect_hits_wall(new_rect):
            self.player.rect.y = new_rect.y

    def distance_to_player(self, x, y):
        return math.hypot(
            self.player.rect.centerx - x,
            self.player.rect.centery - y
        )

    def near_rect(self, rect, distance=INTERACT_DISTANCE):
        return self.distance_to_player(rect.centerx, rect.centery) < distance

    def has_item(self, name):
        return name in self.inventory or name in self.trunk

    def remove_item_anywhere(self, name):
        if name in self.inventory:
            self.inventory.remove(name)
            return True

        if name in self.trunk:
            self.trunk.remove(name)
            return True

        return False

    def interact(self):
        if self.monster.active and self.player_has_toxin:
            self.try_kill_monster()
            return

        if self.note_open:
            self.note_open = False
            self.current_note = None
            return

        for item in self.items:
            if item.collected:
                continue

            if self.distance_to_player(item.x, item.y) < INTERACT_DISTANCE:
                item.collected = True
                self.inventory.append(item.name)
                self.snd_pickup.play()
                self.score += 10
                self.set_message(f"Picked up: {item.name}")
                return

        for note in self.notes:
            if self.distance_to_player(note.x, note.y) < INTERACT_DISTANCE:
                note.read = True
                self.current_note = note
                self.note_open = True
                self.score += 2
                return

        if self.near_rect(self.trunk_rect):
            self.set_message("Trunk: press 1 to store, 2 to take.")
            return

        if self.near_rect(self.generator_rect):
            self.try_generator()
            return

        if self.near_rect(self.main_lab_rect):
            self.try_synthesize_toxin()
            return

        if self.near_rect(self.exit_rect):
            self.try_exit()
            return

        self.set_message("Nothing useful here.")

    def try_generator(self):
        if self.generator_on:
            self.set_message("Generator is already working.")
            return

        if not self.has_item("Fuse A") or not self.has_item("Fuse B"):
            self.set_message("Generator needs Fuse A and Fuse B.")
            return

        self.remove_item_anywhere("Fuse A")
        self.remove_item_anywhere("Fuse B")

        self.generator_on = True
        self.generator_channel.play(self.snd_generator)

        self.monster_wake_pending = True
        self.monster_wake_time = pygame.time.get_ticks() + 8000

        self.score += 50

        self.set_message("Power restored... but something is waking up.", 4200)
        self.set_warning("SYSTEM WARNING: CONTAINMENT SIGNAL LOST", 2500)
        self.start_shake(8, 0.35)

    def try_synthesize_toxin(self):
        if not self.generator_on:
            self.set_message("Main Lab has no power.")
            return

        if self.toxin_ready:
            self.set_message("Toxin is already synthesized.")
            return

        needed = ["Reagent", "Stabilizer", "Tissue Sample"]

        for item in needed:
            if not self.has_item(item):
                self.set_message(f"Missing component: {item}")
                return

        for item in needed:
            self.remove_item_anywhere(item)

        self.toxin_ready = True
        self.player_has_toxin = True

        self.score += 100

        self.set_message("Toxin synthesized. Find F-13 and press E near it.", 4200)
        self.start_shake(10, 0.4)

    def try_kill_monster(self):
        if self.monster_dead:
            self.set_message("F-13 is already dead.")
            return

        if not self.player_has_toxin:
            return

        distance = math.hypot(
            self.player.rect.centerx - self.monster.rect.centerx,
            self.player.rect.centery - self.monster.rect.centery
        )

        if distance > 95:
            return

        self.monster_dead = True
        self.snd_death.play()
        self.monster.active = False
        self.player_has_toxin = False
        self.exit_open = True

        self.clear_warning()
        self.shake_timer = 0
        self.score += 250

        self.set_message("F-13 neutralized. Elevator keycard dropped.", 4200)

        self.items.append(
            Collectible(
                "Keycard",
                self.monster.rect.centerx,
                self.monster.rect.centery,
                self.item_images["Keycard"]
            )
        )

    def try_exit(self):
        if not self.monster_dead:
            self.set_message("You cannot escape while F-13 is alive.")
            return

        if not self.has_item("Keycard"):
            self.set_message("You need the elevator keycard.")
            return

        self.state = "win"

        self.play_menu_music()

        self.score += max(0, 300 - self.game_time())
        self.save_score()

    def store_to_trunk(self):
        if not self.near_rect(self.trunk_rect):
            self.set_message("You are not near the trunk.")
            return

        if not self.inventory:
            self.set_message("Inventory is empty.")
            return

        item = self.inventory.pop()
        self.trunk.append(item)
        self.set_message(f"Stored: {item}")

    def take_from_trunk(self):
        if not self.near_rect(self.trunk_rect):
            self.set_message("You are not near the trunk.")
            return

        if not self.trunk:
            self.set_message("Trunk is empty.")
            return

        item = self.trunk.pop()
        self.inventory.append(item)
        self.set_message(f"Taken: {item}")

    def near_hiding_spot(self):
        for spot in self.hiding_spots:
            if self.near_rect(spot, HIDE_DISTANCE):
                return True

        return False

    def hide(self):
        if not self.near_hiding_spot():
            self.set_message("No hiding spot nearby.")
            return

        self.player.hidden = not self.player.hidden

        if self.player.hidden:
            self.set_message("You are hiding.")

            if self.monster.active:
                self.monster.last_player_pos = None
                self.monster.path = []
                self.monster.path_timer = 0
                self.monster.target_pos = None
                self.clear_warning()
                self.shake_timer = 0

        else:
            self.set_message("You left the hiding spot.")

    def start_shake(self, power=8, duration=0.35):
        self.shake_power = power
        self.shake_timer = duration

    def update_camera(self):
        target_x = self.player.rect.centerx - self.view_w // 2
        target_y = self.player.rect.centery - self.view_h // 2

        smooth = 0.14

        self.camera_x += (target_x - self.camera_x) * smooth
        self.camera_y += (target_y - self.camera_y) * smooth

        self.camera_x = max(0, min(self.camera_x, max(0, self.map_w - self.view_w)))
        self.camera_y = max(0, min(self.camera_y, max(0, self.map_h - self.view_h)))

    def update(self, dt):
        if self.state != "play":
            return

        if self.note_open:
            return

        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0
        moving = False

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= PLAYER_SPEED * dt
            self.player.direction = "up"
            moving = True

        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += PLAYER_SPEED * dt
            self.player.direction = "down"
            moving = True

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= PLAYER_SPEED * dt
            self.player.direction = "left"
            moving = True

        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += PLAYER_SPEED * dt
            self.player.direction = "right"
            moving = True

        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        self.move_player(dx, dy)
        self.update_camera()
        self.player.update_animation(moving, dt)

        if self.monster_wake_pending:
            if pygame.time.get_ticks() >= self.monster_wake_time:
                self.monster_wake_pending = False
                self.generator_channel.fadeout(1500)
                self.monster.activate()
                self.snd_scream.play()
                self.set_message("F-13 is awake. Hide.", 3500)
                self.set_warning("WARNING: F-13 IS ACTIVE", 1800)
                self.start_shake(12, 0.45)

        self.monster.update(
            dt,
            self.player,
            self.is_wall_pixel,
            self.rect_hits_wall
        )

        if self.monster.active:
            d = self.monster_distance()
            monster_state = getattr(self.monster, "state", "patrol")
            self.heartbeat_timer -= dt

            if monster_state == "chase":
                pygame.mixer.music.set_volume(0.35)

                self.monster_sound_timer -= dt

                if self.monster_sound_timer <= 0:
                    self.snd_monster_chase.play()
                    self.monster_sound_timer = 3.5

                if self.heartbeat_timer <= 0:
                    self.snd_heartbeat.play()
                    self.heartbeat_timer = 0.45
            else:
                pygame.mixer.music.set_volume(0.22)

            if self.player.hidden:
                self.clear_warning()

            elif monster_state == "chase":
                self.set_warning("WARNING: F-13 SAW YOU! HIDE!", 650)
                self.start_shake(7, 0.18)

            elif monster_state in ["suspicious", "search"] and d < 420:
                self.set_warning("WARNING: F-13 IS SEARCHING...", 650)

            elif d < 360:
                if self.heartbeat_timer <= 0:
                    self.snd_heartbeat.play()
                    self.heartbeat_timer = 1.1
                self.set_warning("WARNING: F-13 IS CLOSE!", 700)

            else:
                self.monster_sound_timer = 0
                self.clear_warning()
        else:
            self.clear_warning()

        if not self.monster.active:
            self.shake_timer = 0

        elif getattr(self.monster, "state", "") != "chase":
            self.shake_timer = 0

        if self.monster.active and not self.player.hidden:
            catch_distance = math.hypot(
                self.player.rect.centerx - self.monster.rect.centerx,
                self.player.rect.centery - self.monster.rect.centery
            )

            if catch_distance < 45:
                self.snd_heartbeat.stop()

                self.state = "game_over"

                self.play_menu_music()

                self.start_shake(14, 0.5)
                self.save_score()

    def get_camera_offset(self):
        if self.shake_timer <= 0:
            return 0, 0

        return (
            int(math.sin(pygame.time.get_ticks() * 0.08) * self.shake_power),
            int(math.cos(pygame.time.get_ticks() * 0.07) * self.shake_power)
        )

    def draw_text_center(self, text, font, y, color):
        surface = font.render(text, True, color)
        x = SCREEN_W // 2 - surface.get_width() // 2
        self.screen.blit(surface, (x, y))

    def draw_menu(self):
        time = pygame.time.get_ticks()

        bg = pygame.transform.smoothscale(self.map_img, (SCREEN_W, SCREEN_H))
        self.screen.blit(bg, (0, 0))

        dark = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 190))
        self.screen.blit(dark, (0, 0))

        self.draw_text_center("LAB HORROR", self.font_big, 180, (220, 20, 20))
        self.draw_text_center("SUBJECT F-13 HAS ESCAPED", self.font_mid, 285, (230, 230, 230))

        if int(time / 500) % 2 == 0:
            self.draw_text_center("PRESS ENTER TO START", self.font, 420, (255, 255, 255))

        self.draw_text_center(
            "WASD - move | E - interact | H - hide | ESC - quit",
            self.small_font,
            650,
            (180, 180, 180)
        )

    def draw_world(self):
        shake_x, shake_y = self.get_camera_offset()

        cam_x = self.camera_x - shake_x
        cam_y = self.camera_y - shake_y

        view = pygame.Surface((self.view_w, self.view_h)).convert()
        view.blit(self.map_img, (-cam_x, -cam_y))

        for item in self.items:
            item.draw(view, cam_x, cam_y)

        for note in self.notes:
            note.draw(view, cam_x, cam_y)

        self.draw_special_zones(view, cam_x, cam_y)

        self.player.draw(
            view,
            cam_x,
            cam_y,
            self.player_images,
            self.small_font
        )

        if self.monster.active:
            if getattr(self.monster, "state", "") == "chase":
                self.monster.draw(view, cam_x, cam_y, self.monster_chase_img)
            else:
                self.monster.draw(view, cam_x, cam_y, self.monster_img)

        elif self.monster_dead:
            view.blit(
                self.dead_monster_img,
                (
                    self.monster.rect.centerx - cam_x - DEAD_MONSTER_SIZE[0] // 2,
                    self.monster.rect.centery - cam_y - DEAD_MONSTER_SIZE[1] // 2
                )
            )

        scaled = pygame.transform.smoothscale(view, (SCREEN_W, SCREEN_H))
        self.screen.blit(scaled, (0, 0))

    def draw_special_zones(self, surface, cam_x, cam_y):
        zones = [
            (self.trunk_rect, (150, 95, 45), "TRUNK"),
            (self.generator_rect, (220, 180, 50), "GENERATOR"),
            (self.main_lab_rect, (60, 180, 220), "MAIN LAB"),
            (self.exit_rect, (80, 220, 100), "EXIT")
        ]

        for rect, color, label in zones:
            pygame.draw.rect(
                surface,
                color,
                (rect.x - cam_x, rect.y - cam_y, rect.w, rect.h),
                2
            )

            text = self.small_font.render(label, True, color)
            surface.blit(text, (rect.x - cam_x, rect.y - cam_y - 18))

    def draw_darkness(self):
        darkness = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

        if self.generator_on:
            darkness.fill((0, 0, 0, 85))
        else:
            darkness.fill((0, 0, 0, 240))

        px = int((self.player.rect.centerx - self.camera_x) * self.camera_zoom)
        py = int((self.player.rect.centery - self.camera_y) * self.camera_zoom)

        if not self.generator_on:
            radius = 170

            for r in range(radius, 30, -8):
                alpha = int(240 * (1 - r / radius))
                pygame.draw.circle(darkness, (0, 0, 0, alpha), (px, py), r)

            pygame.draw.circle(darkness, (0, 0, 0, 0), (px, py), 58)

        self.screen.blit(darkness, (0, 0))

    def draw_hide_prompt(self):
        if not self.near_hiding_spot():
            return

        time_now = pygame.time.get_ticks()

        if self.player.hidden:
            text_value = "HIDDEN // PRESS H TO LEAVE"
            color = (120, 220, 160)
        else:
            text_value = "PRESS H TO HIDE"
            pulse = 150 + abs(int(105 * math.sin(time_now * 0.009)))
            color = (pulse, 0, 0)

        text = self.font.render(text_value, True, color)
        text = text.convert_alpha()

        if not self.player.hidden:
            alpha = 170 + abs(int(85 * math.sin(time_now * 0.012)))
            text.set_alpha(alpha)

        box_w = text.get_width() + 44
        box_h = 48
        x = SCREEN_W // 2 - box_w // 2
        y = 94

        bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 185))

        self.screen.blit(bg, (x, y))
        pygame.draw.rect(self.screen, (110, 0, 0), (x, y, box_w, box_h), 2, border_radius=8)

        shake_x = 0
        if not self.player.hidden:
            shake_x = int(math.sin(time_now * 0.04) * 2)

        self.screen.blit(
            text,
            (SCREEN_W // 2 - text.get_width() // 2 + shake_x, y + 11)
        )

    def draw_ui(self):
        # Top objective bar
        top = pygame.Surface((SCREEN_W, 92), pygame.SRCALPHA)
        top.fill((0, 0, 0, 175))
        self.screen.blit(top, (0, 0))

        objective = self.get_objective_text()
        obj_text = self.font.render(objective, True, (255, 235, 135))
        self.screen.blit(obj_text, (22, 12))

        status = "POWER ON" if self.generator_on else "POWER OFF"
        toxin = "TOXIN READY" if self.toxin_ready else "NO TOXIN"

        monster_state = getattr(self.monster, "state", "sleeping").upper() if self.monster.active else "SLEEPING"

        self.screen.blit(
            self.small_font.render(
                f"{status} | {toxin} | F-13: {monster_state} | Score: {self.score} | Time: {self.game_time()}s",
                True,
                (220, 220, 220)
            ),
            (22, 48)
        )

        controls_text = "WASD move | E interact | 1 store | 2 take | J save"

        if self.near_hiding_spot():
            controls_text += " | H hide"

        self.screen.blit(
            self.small_font.render(
                controls_text,
                True,
                (170, 170, 170)
            ),
            (760, 18)
        )

        # Compact inventory on the right side, so it does not cover the player.
        inv_box = pygame.Rect(SCREEN_W - 190, 112, 170, 355)
        inv_bg = pygame.Surface((inv_box.w, inv_box.h), pygame.SRCALPHA)
        inv_bg.fill((10, 10, 16, 135))
        self.screen.blit(inv_bg, (inv_box.x, inv_box.y))
        pygame.draw.rect(self.screen, (115, 115, 135), inv_box, 2, border_radius=14)

        title = self.small_font.render("BAG", True, (230, 230, 240))
        self.screen.blit(title, (inv_box.x + 16, inv_box.y + 10))

        slot_size = 44
        gap = 10
        start_x = inv_box.x + 16
        start_y = inv_box.y + 40

        visible_items = self.inventory[:10]
        for i in range(10):
            col = i % 3
            row = i // 3
            slot = pygame.Rect(start_x + col * (slot_size + gap), start_y + row * 66, slot_size, slot_size)
            pygame.draw.rect(self.screen, (28, 28, 38), slot, border_radius=9)
            pygame.draw.rect(self.screen, (95, 95, 110), slot, 1, border_radius=9)

            if i < len(visible_items):
                name = visible_items[i]
                img = self.item_images.get(name)
                if img:
                    small = pygame.transform.smoothscale(img, (30, 30))
                    self.screen.blit(small, (slot.centerx - 15, slot.centery - 18))

                label = self.small_font.render(name[:5], True, (235, 235, 235))
                self.screen.blit(label, (slot.centerx - label.get_width() // 2, slot.bottom + 2))

        if not self.inventory:
            empty = self.small_font.render("empty", True, (150, 150, 160))
            self.screen.blit(empty, (inv_box.x + 62, inv_box.y + 175))

        trunk_text = ", ".join(self.trunk) if self.trunk else "empty"
        trunk_bg = pygame.Surface((370, 34), pygame.SRCALPHA)
        trunk_bg.fill((0, 0, 0, 120))
        self.screen.blit(trunk_bg, (18, SCREEN_H - 48))
        trunk = self.small_font.render(f"TRUNK: {trunk_text}", True, (190, 190, 200))
        self.screen.blit(trunk, (30, SCREEN_H - 39))

        self.draw_hide_prompt()

        if self.message and pygame.time.get_ticks() < self.message_until:
            msg_bg = pygame.Surface((SCREEN_W, 44), pygame.SRCALPHA)
            msg_bg.fill((0, 0, 0, 150))
            self.screen.blit(msg_bg, (0, 100))

            msg = self.font.render(self.message, True, (255, 230, 120))
            self.screen.blit(msg, (SCREEN_W // 2 - msg.get_width() // 2, 110))

    def draw_warning(self):
        if not self.warning_text or pygame.time.get_ticks() >= self.warning_until:
            return

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((180, 0, 0, 58))
        self.screen.blit(overlay, (0, 0))

        if int(pygame.time.get_ticks() / 130) % 2 == 0:
            text = self.font_mid.render(self.warning_text, True, (255, 40, 40))
            x = SCREEN_W // 2 - text.get_width() // 2
            self.screen.blit(text, (x, 150))

    def draw_note_box(self):
        if not self.current_note:
            return

        box = pygame.Rect(230, 150, 820, 360)

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        pygame.draw.rect(self.screen, (18, 18, 22), box)
        pygame.draw.rect(self.screen, (230, 230, 230), box, 3)

        title = self.font_mid.render(self.current_note.title, True, (255, 255, 255))
        self.screen.blit(title, (box.x + 35, box.y + 35))

        words = self.current_note.text.split()
        lines = []
        current = ""

        for word in words:
            test = current + word + " "

            if self.font.size(test)[0] < box.width - 70:
                current = test
            else:
                lines.append(current)
                current = word + " "

        lines.append(current)

        y = box.y + 110

        for line in lines:
            text = self.font.render(line, True, (220, 220, 220))
            self.screen.blit(text, (box.x + 35, y))
            y += 32

        hint = self.small_font.render("Press E to close", True, (170, 170, 170))
        self.screen.blit(hint, (box.x + 35, box.bottom - 45))

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((120, 0, 0, 175))
        self.screen.blit(overlay, (0, 0))

        self.draw_text_center("YOU WERE CAUGHT", self.font_big, 250, (255, 255, 255))
        self.draw_text_center("F-13 found you in the dark.", self.font, 360, (230, 230, 230))
        self.draw_text_center("PRESS R TO RESTART", self.font, 440, (255, 255, 255))

    def draw_win(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 80, 55, 175))
        self.screen.blit(overlay, (0, 0))

        self.draw_text_center("ESCAPE SUCCESSFUL", self.font_big, 230, (255, 255, 255))
        self.draw_text_center(f"Score: {self.score}", self.font_mid, 340, (230, 255, 230))
        self.draw_text_center(f"Time: {self.game_time()} sec", self.font, 395, (220, 240, 220))
        self.draw_text_center("PRESS R TO PLAY AGAIN", self.font, 470, (255, 255, 255))

    def draw(self):
        self.draw_world()
        self.draw_darkness()
        self.draw_warning()
        self.draw_ui()

        if self.note_open:
            self.draw_note_box()

        if self.state == "game_over":
            self.draw_game_over()

        elif self.state == "win":
            self.draw_win()