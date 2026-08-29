"""
GRIM TROOPER - a retro-style run-and-gun platformer
Grimdark sci-fi theme, pixel-art shapes (no external assets needed)

Controls:
  A / D or Left / Right - move
  SPACE - jump
  J or Left-Click - fire current weapon
  1 - Bolter (gun)   2 - Chain Blade (melee)   3 - Frag (grenade)
  F11 - toggle fullscreen
  ESC - quit

Levels 1-2 fit on one screen. From level 3 onward, the map grows wider
and the camera scrolls to follow you.

High scores are saved locally next to this script in
grim_trooper_scores.json.

Run with:  pip install pygame
           python grim_trooper.py
"""

import pygame
import random
import sys
import math
import json
import os

pygame.init()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCREEN_W, SCREEN_H = 960, 540   # fixed internal render resolution
FPS = 60
GRAVITY = 0.7
JUMP_STRENGTH = -14
PLAYER_SPEED = 5
BULLET_SPEED = 12
SEGMENT_WIDTH = 480  # how much extra width each level beyond 2 adds
MAX_NAME_LEN = 14

SCORES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grim_trooper_scores.json")

# Retro grimdark palette
COL_BG_FAR = (18, 14, 22)
COL_BG_NEAR = (32, 22, 28)
COL_GROUND = (54, 40, 36)
COL_GROUND_EDGE = (90, 60, 40)

COL_PLAYER = (150, 30, 30)        # crimson armor
COL_PLAYER_TRIM = (200, 170, 60)  # gold trim
COL_PLAYER_VISOR = (255, 220, 120)
COL_MELEE = (240, 230, 200)

COL_BULLET_PLAYER = (255, 210, 90)
COL_BULLET_ENEMY = (140, 255, 140)
COL_GRENADE = (80, 90, 40)
COL_EXPLOSION = (255, 140, 40)
COL_UI_TEXT = (220, 200, 160)
COL_HEALTH = (170, 30, 30)
COL_HEALTH_BG = (60, 20, 20)

# ---------------------------------------------------------------------------
# Level background themes - one rotates in per level (level 11 repeats theme 1)
# ---------------------------------------------------------------------------
BACKGROUND_THEMES = [
    {
        "name": "Ashen Wastes", "sky_far": (18, 14, 22), "sky_near": (60, 46, 40),
        "ground": (54, 40, 36), "ground_edge": (90, 60, 40),
        "skyline_style": "blocks", "particle_color": (110, 100, 95), "orb": None,
    },
    {
        "name": "Toxic Marshes", "sky_far": (10, 22, 14), "sky_near": (30, 66, 38),
        "ground": (32, 46, 26), "ground_edge": (70, 110, 50),
        "skyline_style": "domes", "particle_color": (120, 220, 120), "orb": None,
    },
    {
        "name": "Frozen Reach", "sky_far": (14, 20, 30), "sky_near": (70, 100, 130),
        "ground": (60, 70, 90), "ground_edge": (170, 200, 220),
        "skyline_style": "spikes", "particle_color": (230, 240, 255), "orb": None,
    },
    {
        "name": "Void Rift", "sky_far": (8, 6, 16), "sky_near": (40, 20, 60),
        "ground": (30, 20, 40), "ground_edge": (110, 70, 160),
        "skyline_style": "towers", "particle_color": (200, 170, 255),
        "orb": ((60, 30, 80), 46, 0.18),
    },
    {
        "name": "Molten Forge", "sky_far": (30, 10, 6), "sky_near": (110, 40, 20),
        "ground": (60, 30, 20), "ground_edge": (230, 120, 30),
        "skyline_style": "blocks", "particle_color": (255, 160, 60),
        "orb": ((200, 70, 30), 34, 0.16),
    },
    {
        "name": "Bone Fields", "sky_far": (26, 22, 18), "sky_near": (90, 80, 66),
        "ground": (80, 70, 56), "ground_edge": (200, 190, 160),
        "skyline_style": "ruins", "particle_color": (210, 200, 180), "orb": None,
    },
    {
        "name": "Blood Moon", "sky_far": (20, 6, 8), "sky_near": (80, 20, 24),
        "ground": (50, 22, 22), "ground_edge": (150, 40, 40),
        "skyline_style": "spikes", "particle_color": (200, 80, 70),
        "orb": ((160, 30, 30), 40, 0.15),
    },
    {
        "name": "Rust Sector", "sky_far": (24, 16, 10), "sky_near": (100, 60, 30),
        "ground": (70, 44, 24), "ground_edge": (200, 120, 50),
        "skyline_style": "towers", "particle_color": (230, 150, 70), "orb": None,
    },
    {
        "name": "Abyssal Depths", "sky_far": (4, 14, 16), "sky_near": (10, 50, 54),
        "ground": (14, 40, 42), "ground_edge": (40, 130, 130),
        "skyline_style": "domes", "particle_color": (80, 220, 210), "orb": None,
    },
    {
        "name": "Golden Reliquary", "sky_far": (22, 16, 6), "sky_near": (90, 70, 20),
        "ground": (70, 54, 20), "ground_edge": (220, 180, 60),
        "skyline_style": "ruins", "particle_color": (240, 210, 120),
        "orb": ((200, 170, 90), 30, 0.14),
    },
]


def theme_for_level(level):
    return BACKGROUND_THEMES[(level - 1) % len(BACKGROUND_THEMES)]

# Actual OS window; the game always draws onto the fixed-size `canvas` and
# that canvas is scaled + letterboxed onto this each frame, so fullscreen
# just changes presentation, not any gameplay coordinates.
display_surface = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("GRIM TROOPER")
canvas = pygame.Surface((SCREEN_W, SCREEN_H))
is_fullscreen = False

clock = pygame.time.Clock()
font_big = pygame.font.SysFont("couriernew", 48, bold=True)
font_med = pygame.font.SysFont("couriernew", 24, bold=True)
font_small = pygame.font.SysFont("couriernew", 16, bold=True)


def toggle_fullscreen():
    global display_surface, is_fullscreen
    is_fullscreen = not is_fullscreen
    if is_fullscreen:
        display_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        display_surface = pygame.display.set_mode((SCREEN_W, SCREEN_H))


def present():
    """Scale the fixed-resolution canvas onto the real window, centered
    with letterboxing so aspect ratio never distorts."""
    disp_w, disp_h = display_surface.get_size()
    scale = max(0.01, min(disp_w / SCREEN_W, disp_h / SCREEN_H))
    new_w, new_h = max(1, int(SCREEN_W * scale)), max(1, int(SCREEN_H * scale))
    scaled = pygame.transform.smoothscale(canvas, (new_w, new_h))
    display_surface.fill((0, 0, 0))
    x = (disp_w - new_w) // 2
    y = (disp_h - new_h) // 2
    display_surface.blit(scaled, (x, y))
    pygame.display.flip()


# ---------------------------------------------------------------------------
# Score persistence
# ---------------------------------------------------------------------------
def load_scores():
    try:
        with open(SCORES_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return []


def save_score(name, score, level):
    scores = load_scores()
    scores.append({"name": (name.strip() or "TROOPER")[:MAX_NAME_LEN], "score": score, "level": level})
    scores.sort(key=lambda e: e.get("score", 0), reverse=True)
    scores = scores[:20]
    try:
        with open(SCORES_FILE, "w") as f:
            json.dump(scores, f, indent=2)
    except OSError:
        pass
    return scores


# ---------------------------------------------------------------------------
# Enemy type definitions
# ---------------------------------------------------------------------------
ENEMY_TYPES = {
    "grunt": {
        "health": 30, "speed": 1.5, "size": (34, 44),
        "color": (60, 140, 70), "accent": (220, 40, 40),
        "cooldown": (90, 180), "score": 100, "shape": "rect", "bullet_dmg": 10,
    },
    "scout": {
        "health": 15, "speed": 3.2, "size": (26, 30),
        "color": (150, 150, 60), "accent": (255, 240, 120),
        "cooldown": (60, 120), "score": 150, "shape": "triangle", "bullet_dmg": 6,
    },
    "heavy": {
        "health": 70, "speed": 0.8, "size": (46, 56),
        "color": (90, 70, 130), "accent": (200, 100, 255),
        "cooldown": (50, 100), "score": 250, "shape": "hex", "bullet_dmg": 16,
    },
}

WEAPON_ORDER = ["gun", "melee", "grenade"]
WEAPON_NAMES = {"gun": "BOLTER", "melee": "CHAIN BLADE", "grenade": "FRAG"}


# ---------------------------------------------------------------------------
# Projectiles / effects
# ---------------------------------------------------------------------------
class Bullet:
    def __init__(self, x, y, direction, from_player=True, dmg=10):
        self.rect = pygame.Rect(x, y, 10, 4)
        self.direction = direction
        self.from_player = from_player
        self.dmg = dmg
        self.alive = True

    def update(self, level_width):
        self.rect.x += BULLET_SPEED * self.direction
        if self.rect.x < -20 or self.rect.x > level_width + 20:
            self.alive = False

    def draw(self, surf, camera_x):
        color = COL_BULLET_PLAYER if self.from_player else COL_BULLET_ENEMY
        pygame.draw.rect(surf, color, self.rect.move(-camera_x, 0))


class Grenade:
    def __init__(self, x, y, direction):
        self.rect = pygame.Rect(x, y, 10, 10)
        self.vx = 7 * direction
        self.vy = -11
        self.fuse = 70
        self.alive = True
        self.exploded = False

    def update(self, platforms, level_width):
        if self.exploded:
            return
        self.vy += GRAVITY
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)

        for p in platforms:
            if self.rect.colliderect(p):
                self.exploded = True
                return

        self.fuse -= 1
        if self.fuse <= 0:
            self.exploded = True

        if self.rect.x < -30 or self.rect.x > level_width + 30:
            self.alive = False

    def draw(self, surf, camera_x):
        if not self.exploded:
            pygame.draw.circle(surf, COL_GRENADE, self.rect.move(-camera_x, 0).center, 5)


class Explosion:
    RADIUS = 70
    LIFETIME = 14

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = self.LIFETIME
        self.alive = True

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.alive = False

    def draw(self, surf, camera_x):
        progress = 1 - (self.timer / self.LIFETIME)
        radius = int(self.RADIUS * progress)
        alpha_surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        fade = max(0, 255 - int(255 * progress))
        pygame.draw.circle(alpha_surf, (*COL_EXPLOSION, fade), (radius + 2, radius + 2), radius, width=4)
        surf.blit(alpha_surf, (self.x - camera_x - radius - 2, self.y - radius - 2))


class Powerup:
    """Armor and grenade pickups scattered across the map."""

    def __init__(self, x, y, ptype):
        self.rect = pygame.Rect(x, y, 22, 22)
        self.ptype = ptype  # "armor" or "grenade"
        self.alive = True
        self.bob_seed = random.uniform(0, math.pi * 2)

    def draw(self, surf, camera_x):
        bob = int(3 * math.sin(pygame.time.get_ticks() / 250 + self.bob_seed))
        r = self.rect.move(-camera_x, bob)
        if r.right < 0 or r.left > SCREEN_W:
            return
        if self.ptype == "armor":
            pygame.draw.rect(surf, (60, 50, 60), r, border_radius=5)
            pygame.draw.rect(surf, (210, 210, 225), r.inflate(-4, -4), border_radius=4)
            pygame.draw.rect(surf, (170, 30, 30), (r.centerx - 2, r.top + 4, 4, r.height - 8))
            pygame.draw.rect(surf, (170, 30, 30), (r.left + 4, r.centery - 2, r.width - 8, 4))
        else:
            pygame.draw.circle(surf, (30, 25, 20), r.center, 11)
            pygame.draw.circle(surf, COL_GRENADE, r.center, 9)
            pygame.draw.rect(surf, (150, 140, 60), (r.centerx - 2, r.top, 4, 5))


# ---------------------------------------------------------------------------
# Enemy
# ---------------------------------------------------------------------------
class Enemy:
    def __init__(self, x, y, patrol_min, patrol_max, etype, difficulty=1.0):
        spec = ENEMY_TYPES[etype]
        self.etype = etype
        self.shape = spec["shape"]
        w, h = spec["size"]
        self.rect = pygame.Rect(x, y, w, h)
        self.speed = spec["speed"] * (1 + 0.12 * (difficulty - 1))
        self.vx = self.speed
        self.patrol_min = patrol_min
        self.patrol_max = patrol_max
        self.max_health = int(spec["health"] * (1 + 0.18 * (difficulty - 1)))
        self.health = self.max_health
        self.color = spec["color"]
        self.accent = spec["accent"]
        self.score_value = spec["score"]
        self.bullet_dmg = spec["bullet_dmg"]
        self.alive = True
        cd_min, cd_max = spec["cooldown"]
        self.shoot_cooldown = random.randint(cd_min, cd_max)
        self.cd_range = (max(20, int(cd_min / (1 + 0.1 * (difficulty - 1)))),
                          max(40, int(cd_max / (1 + 0.1 * (difficulty - 1)))))
        self.facing = -1

    def update(self, bullets):
        self.rect.x += self.vx
        if self.rect.x <= self.patrol_min or self.rect.x >= self.patrol_max:
            self.vx *= -1
            self.facing = 1 if self.vx > 0 else -1

        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = random.randint(*self.cd_range)
            bx = self.rect.centerx
            by = self.rect.centery
            bullets.append(Bullet(bx, by, self.facing, from_player=False, dmg=self.bullet_dmg))

    def draw(self, surf, camera_x):
        r = self.rect.move(-camera_x, 0)
        if self.shape == "rect":
            pygame.draw.rect(surf, self.color, r, border_radius=3)
            eye_x = r.centerx + (6 if self.facing > 0 else -6)
            pygame.draw.rect(surf, self.accent, (eye_x - 3, r.y + 10, 6, 6))
        elif self.shape == "triangle":
            points = [(r.centerx, r.top), (r.left, r.bottom), (r.right, r.bottom)]
            pygame.draw.polygon(surf, self.color, points)
            pygame.draw.circle(surf, self.accent, (r.centerx, r.centery + 4), 3)
        elif self.shape == "hex":
            cx, cy = r.centerx, r.centery
            rad_x, rad_y = r.width / 2, r.height / 2
            points = []
            for i in range(6):
                angle = math.pi / 3 * i - math.pi / 6
                points.append((cx + rad_x * math.cos(angle), cy + rad_y * math.sin(angle)))
            pygame.draw.polygon(surf, self.color, points)
            eye_x = cx + (8 if self.facing > 0 else -8)
            pygame.draw.rect(surf, self.accent, (eye_x - 4, cy - 4, 8, 8))

        pip_w = int(30 * (self.health / self.max_health))
        pygame.draw.rect(surf, COL_HEALTH_BG, (r.x, r.y - 8, 30, 4))
        pygame.draw.rect(surf, COL_HEALTH, (r.x, r.y - 8, pip_w, 4))

    def take_hit(self, dmg):
        self.health -= dmg
        if self.health <= 0:
            self.alive = False


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------
class Player:
    """Drawn as an angular armored silhouette (polygon), distinct from the
    rectangular/triangular/hex enemy shapes. World-space position; the
    camera offset is applied only at draw time."""

    def __init__(self, x, y, name="TROOPER"):
        self.name = name
        self.rect = pygame.Rect(x, y, 32, 48)
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.facing = 1
        self.health = 100
        self.max_health = 100
        self.score = 0

        self.weapon_index = 0
        self.gun_cooldown = 0
        self.melee_cooldown = 0
        self.melee_flash = 0
        self.grenade_cooldown = 0
        self.grenade_count = 3

        self.levels_cleared = 0  # scales bolter/blade damage as you progress

        self.invuln = 0

    @property
    def weapon(self):
        return WEAPON_ORDER[self.weapon_index]

    def switch_weapon(self, index):
        if 0 <= index < len(WEAPON_ORDER):
            self.weapon_index = index

    def handle_input(self, keys, level_width):
        self.vx = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vx = -PLAYER_SPEED
            self.facing = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vx = PLAYER_SPEED
            self.facing = 1
        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
            self.vy = JUMP_STRENGTH
            self.on_ground = False

        if self.gun_cooldown > 0:
            self.gun_cooldown -= 1
        if self.melee_cooldown > 0:
            self.melee_cooldown -= 1
        if self.grenade_cooldown > 0:
            self.grenade_cooldown -= 1
        if self.melee_flash > 0:
            self.melee_flash -= 1

    def fire(self, bullets, grenades, enemies):
        weapon = self.weapon
        if weapon == "gun":
            if self.gun_cooldown == 0:
                self.gun_cooldown = 14
                dmg = 15 + self.levels_cleared * 3
                bx = self.rect.centerx + (20 * self.facing)
                by = self.rect.centery - 4
                bullets.append(Bullet(bx, by, self.facing, from_player=True, dmg=dmg))

        elif weapon == "melee":
            if self.melee_cooldown == 0:
                self.melee_cooldown = 25
                self.melee_flash = 8
                dmg = 35 + self.levels_cleared * 5
                reach = 40
                if self.facing > 0:
                    hit_rect = pygame.Rect(self.rect.right, self.rect.top, reach, self.rect.height)
                else:
                    hit_rect = pygame.Rect(self.rect.left - reach, self.rect.top, reach, self.rect.height)
                for e in enemies:
                    if e.alive and hit_rect.colliderect(e.rect):
                        e.take_hit(dmg)
                        if not e.alive:
                            self.score += e.score_value

        elif weapon == "grenade":
            if self.grenade_cooldown == 0 and self.grenade_count > 0:
                self.grenade_cooldown = 45
                self.grenade_count -= 1
                gx = self.rect.centerx + (10 * self.facing)
                gy = self.rect.top
                grenades.append(Grenade(gx, gy, self.facing))

    def update(self, platforms, level_width):
        self.vy += GRAVITY
        if self.vy > 18:
            self.vy = 18

        self.rect.x += self.vx
        self._collide(platforms, dx=self.vx)

        self.rect.y += self.vy
        self.on_ground = False
        self._collide(platforms, dy=self.vy)

        if self.invuln > 0:
            self.invuln -= 1

        self.rect.x = max(0, min(self.rect.x, level_width - self.rect.width))
        if self.rect.y > SCREEN_H:
            self.take_damage(100)

    def _collide(self, platforms, dx=0, dy=0):
        for p in platforms:
            if self.rect.colliderect(p):
                if dy > 0:
                    self.rect.bottom = p.top
                    self.vy = 0
                    self.on_ground = True
                elif dy < 0:
                    self.rect.top = p.bottom
                    self.vy = 0
                elif dx > 0:
                    self.rect.right = p.left
                elif dx < 0:
                    self.rect.left = p.right

    def take_damage(self, dmg):
        if self.invuln > 0:
            return
        self.health -= dmg
        self.invuln = 45
        if self.health < 0:
            self.health = 0

    def draw(self, surf, camera_x):
        r = self.rect.move(-camera_x, 0)
        color = COL_PLAYER
        if self.invuln > 0 and (self.invuln // 4) % 2 == 0:
            color = (255, 255, 255)

        if self.facing >= 0:
            points = [
                (r.left + 8, r.top),
                (r.right - 4, r.top + 6),
                (r.right, r.top + 18),
                (r.right - 6, r.centery),
                (r.right - 10, r.bottom),
                (r.left + 6, r.bottom),
                (r.left, r.centery + 4),
                (r.left + 2, r.top + 16),
            ]
        else:
            points = [
                (r.right - 8, r.top),
                (r.left + 4, r.top + 6),
                (r.left, r.top + 18),
                (r.left + 6, r.centery),
                (r.left + 10, r.bottom),
                (r.right - 6, r.bottom),
                (r.right, r.centery + 4),
                (r.right - 2, r.top + 16),
            ]
        pygame.draw.polygon(surf, color, points)

        trim_y = r.top + 20
        pygame.draw.line(surf, COL_PLAYER_TRIM, (r.left + 2, trim_y), (r.right - 2, trim_y), 3)
        visor_x = r.centerx + (4 if self.facing > 0 else -4)
        pygame.draw.rect(surf, COL_PLAYER_VISOR, (visor_x - 6, r.top + 6, 12, 4))

        if self.weapon == "gun":
            gun_x = r.centerx + (18 * self.facing)
            pygame.draw.rect(surf, (30, 30, 30), (min(gun_x, r.centerx), r.centery - 3, 20, 6))
        elif self.weapon == "melee":
            blade_x = r.centerx + (16 * self.facing)
            pygame.draw.line(surf, (180, 180, 190), (r.centerx, r.centery), (blade_x, r.centery), 4)
            if self.melee_flash > 0:
                reach = 40
                fx = r.right if self.facing > 0 else r.left - reach
                flash_rect = pygame.Rect(fx, r.top, reach, r.height)
                flash_surf = pygame.Surface((flash_rect.width, flash_rect.height), pygame.SRCALPHA)
                alpha = int(200 * (self.melee_flash / 8))
                pygame.draw.rect(flash_surf, (*COL_MELEE, alpha), flash_surf.get_rect())
                surf.blit(flash_surf, flash_rect.topleft)
        elif self.weapon == "grenade":
            gx = r.centerx + (14 * self.facing)
            pygame.draw.circle(surf, COL_GRENADE, (gx, r.centery), 5)


# ---------------------------------------------------------------------------
# Level building
# ---------------------------------------------------------------------------
BASE_PLATFORMS = [
    pygame.Rect(150, 420, 160, 20),
    pygame.Rect(400, 350, 160, 20),
    pygame.Rect(650, 280, 160, 20),
    pygame.Rect(250, 220, 140, 20),
    pygame.Rect(50, 300, 120, 20),
]

BASE_SPAWN_SLOTS = [
    (420, 306, 400, 540),
    (680, 236, 650, 790),
    (700, SCREEN_H - 84, 600, 900),
    (250, 176, 260, 380),
    (60, 256, 50, 160),
    (170, 376, 150, 300),
]

PLATFORM_HEIGHTS = [220, 280, 350, 420]


def _scatter_powerups(platforms, rng, count):
    non_ground = platforms[1:]
    if not non_ground:
        return []
    count = min(count, len(non_ground))
    chosen = rng.sample(non_ground, k=count)
    specs = []
    for p in chosen:
        ptype = "armor" if rng.random() < 0.55 else "grenade"
        x = p.centerx - 11
        y = p.top - 26
        specs.append((x, y, ptype))
    return specs


def build_level(level):
    """Returns (platforms, spawn_slots, level_width, powerup_specs).
    Levels 1-2 are identical to the original single-screen layout.
    From level 3 on, the map grows by SEGMENT_WIDTH per level and gains
    extra procedurally-placed platforms/enemy spawn points/powerups."""
    if level <= 2:
        level_width = SCREEN_W
        platforms = [pygame.Rect(0, SCREEN_H - 40, level_width, 40)]
        platforms += [p.copy() for p in BASE_PLATFORMS]
        spawn_slots = list(BASE_SPAWN_SLOTS)
        rng = random.Random(500 + level)
        powerup_specs = _scatter_powerups(platforms, rng, count=2)
        return platforms, spawn_slots, level_width, powerup_specs

    num_segments = level - 2
    level_width = SCREEN_W + num_segments * SEGMENT_WIDTH

    platforms = [pygame.Rect(0, SCREEN_H - 40, level_width, 40)]
    platforms += [p.copy() for p in BASE_PLATFORMS]
    spawn_slots = list(BASE_SPAWN_SLOTS)

    rng = random.Random(1000 + level)
    x_cursor = SCREEN_W
    for _ in range(num_segments):
        num_p = rng.randint(2, 3)
        for _ in range(num_p):
            w = rng.randint(120, 180)
            x = x_cursor + rng.randint(20, SEGMENT_WIDTH - w - 20)
            y = rng.choice(PLATFORM_HEIGHTS)
            platforms.append(pygame.Rect(x, y, w, 20))
            patrol_min = x + 4
            patrol_max = x + w - 38
            if patrol_max > patrol_min:
                spawn_slots.append((x + 10, y - 44, patrol_min, patrol_max))
        x_cursor += SEGMENT_WIDTH

    powerup_specs = _scatter_powerups(platforms, rng, count=2 + num_segments)
    return platforms, spawn_slots, level_width, powerup_specs


def spawn_wave(level, spawn_slots):
    difficulty = level
    num_enemies = min(len(spawn_slots), 2 + level)

    pool = ["grunt"] * 5
    if level >= 2:
        pool += ["scout"] * 3
    if level >= 4:
        pool += ["heavy"] * 2

    enemies = []
    slots = random.sample(spawn_slots, k=min(num_enemies, len(spawn_slots)))
    for (x, y, pmin, pmax) in slots:
        etype = random.choice(pool)
        enemies.append(Enemy(x, y, pmin, pmax, etype, difficulty=difficulty))
    return enemies


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def get_camera_x(player, level_width):
    cam = player.rect.centerx - SCREEN_W // 2
    return max(0, min(cam, max(0, level_width - SCREEN_W)))


def _draw_skyline_shape(surf, style, x, y_base, w, h, color):
    if style == "blocks":
        pygame.draw.rect(surf, color, (x, y_base - h, w, h))
    elif style == "spikes":
        points = [(x, y_base), (x + w / 2, y_base - h), (x + w, y_base)]
        pygame.draw.polygon(surf, color, points)
    elif style == "domes":
        pygame.draw.rect(surf, color, (x, y_base - h * 0.5, w, h * 0.5))
        pygame.draw.circle(surf, color, (int(x + w / 2), int(y_base - h * 0.5)), int(w / 2))
    elif style == "towers":
        tower_w = max(6, int(w * 0.3))
        pygame.draw.rect(surf, color, (x + w / 2 - tower_w / 2, y_base - h, tower_w, h))
        pygame.draw.line(surf, color, (x + w / 2, y_base - h), (x + w / 2, y_base - h - 14), 2)
    elif style == "ruins":
        jag = h * 0.2
        points = [
            (x, y_base), (x, y_base - h + jag), (x + w * 0.3, y_base - h),
            (x + w * 0.6, y_base - h + jag * 1.5), (x + w, y_base - h * 0.7), (x + w, y_base),
        ]
        pygame.draw.polygon(surf, color, points)


def draw_background(surf, camera_x, theme):
    surf.fill(theme["sky_far"])

    if theme.get("orb"):
        ocolor, oradius, oy_frac = theme["orb"]
        ox = int(SCREEN_W * 0.78 - camera_x * 0.05)
        oy = int(SCREEN_H * oy_frac)
        pygame.draw.circle(surf, ocolor, (ox, oy), oradius)

    pcolor = theme.get("particle_color")
    if pcolor:
        rng = random.Random(hash(theme["name"]) % 100000)
        for _ in range(18):
            px = (rng.randint(0, SCREEN_W + 200) - camera_x * 0.15) % (SCREEN_W + 200) - 100
            py = rng.randint(20, SCREEN_H - 60)
            size = rng.choice([1, 1, 2])
            pygame.draw.circle(surf, pcolor, (int(px), py), size)

    style = theme["skyline_style"]
    for i in range(20):
        x = (i * 110 - camera_x * 0.3) % (SCREEN_W + 110) - 55
        h = 80 + (i * 37) % 140
        _draw_skyline_shape(surf, style, x, SCREEN_H - 40, 60, h, theme["sky_near"])

    pygame.draw.rect(surf, theme["ground"], (0, SCREEN_H - 40, SCREEN_W, 40))
    pygame.draw.rect(surf, theme["ground_edge"], (0, SCREEN_H - 40, SCREEN_W, 4))


def draw_platforms(surf, platforms, camera_x, theme):
    for p in platforms[1:]:
        r = p.move(-camera_x, 0)
        if r.right < 0 or r.left > SCREEN_W:
            continue
        pygame.draw.rect(surf, theme["ground"], r)
        pygame.draw.rect(surf, theme["ground_edge"], (r.x, r.y, r.width, 3))


def draw_ui(surf, player, level, theme):
    pygame.draw.rect(surf, COL_HEALTH_BG, (20, 20, 200, 20))
    hp_w = int(200 * (player.health / player.max_health))
    pygame.draw.rect(surf, COL_HEALTH, (20, 20, hp_w, 20))
    surf.blit(font_small.render("ARMOR", True, COL_UI_TEXT), (24, 22))
    surf.blit(font_med.render(f"SCORE {player.score}", True, COL_UI_TEXT), (20, 50))
    surf.blit(font_small.render(f"LEVEL {level}", True, COL_UI_TEXT), (SCREEN_W - 110, 20))
    surf.blit(font_small.render(theme["name"], True, (150, 130, 100)), (SCREEN_W - 200, 96))
    surf.blit(font_small.render(player.name, True, (140, 120, 90)), (SCREEN_W - 110, 76))

    weapon_label = f"{WEAPON_NAMES[player.weapon]}"
    if player.weapon == "grenade":
        weapon_label += f"  x{player.grenade_count}"
    elif player.weapon in ("gun", "melee"):
        weapon_label += f"  Lv{player.levels_cleared + 1}"
    surf.blit(font_small.render(weapon_label, True, COL_UI_TEXT), (SCREEN_W - 220, 44))
    surf.blit(font_small.render("[1] BOLTER  [2] BLADE  [3] FRAG", True, (140, 120, 90)),
              (SCREEN_W // 2 - 140, SCREEN_H - 22))


def show_message(lines, sub=None):
    canvas.fill((10, 8, 10))
    for i, line in enumerate(lines):
        text = font_big.render(line, True, COL_UI_TEXT)
        canvas.blit(text, text.get_rect(center=(SCREEN_W // 2, 200 + i * 60)))
    if sub:
        subtext = font_med.render(sub, True, (150, 130, 100))
        canvas.blit(subtext, subtext.get_rect(center=(SCREEN_W // 2, 360)))
    present()


def draw_menu(name_input, cursor_on, top_scores):
    draw_background(canvas, 0, BACKGROUND_THEMES[0])
    title = font_big.render("GRIM TROOPER", True, COL_UI_TEXT)
    canvas.blit(title, title.get_rect(center=(SCREEN_W // 2, 90)))

    prompt = font_med.render("ENTER YOUR NAME:", True, COL_UI_TEXT)
    canvas.blit(prompt, prompt.get_rect(center=(SCREEN_W // 2, 170)))

    box = pygame.Rect(0, 0, 320, 40)
    box.center = (SCREEN_W // 2, 210)
    pygame.draw.rect(canvas, (40, 30, 30), box, border_radius=4)
    pygame.draw.rect(canvas, COL_PLAYER_TRIM, box, width=2, border_radius=4)
    display_name = name_input + ("_" if cursor_on else "")
    name_text = font_med.render(display_name, True, (240, 230, 210))
    canvas.blit(name_text, name_text.get_rect(midleft=(box.left + 14, box.centery)))

    hint = font_small.render("ENTER to begin   F11 fullscreen   ESC to quit", True, (150, 130, 100))
    canvas.blit(hint, hint.get_rect(center=(SCREEN_W // 2, 260)))

    lb_title = font_small.render("TOP SCORES", True, COL_UI_TEXT)
    canvas.blit(lb_title, lb_title.get_rect(center=(SCREEN_W // 2, 310)))
    for i, entry in enumerate(top_scores[:5]):
        line = f"{i + 1}. {entry.get('name', '???'):<14} {entry.get('score', 0):>6}  Lv{entry.get('level', 1)}"
        text = font_small.render(line, True, (190, 170, 140))
        canvas.blit(text, text.get_rect(center=(SCREEN_W // 2, 336 + i * 20)))

    present()


def draw_leaderboard(scores, latest_entry):
    canvas.fill((10, 8, 10))
    title = font_big.render("LEADERBOARD", True, COL_UI_TEXT)
    canvas.blit(title, title.get_rect(center=(SCREEN_W // 2, 70)))

    for i, entry in enumerate(scores[:10]):
        is_latest = latest_entry is not None and entry is latest_entry
        color = (255, 220, 140) if is_latest else (200, 185, 160)
        line = f"{i + 1:>2}. {entry.get('name', '???'):<14} {entry.get('score', 0):>6}   Lv{entry.get('level', 1)}"
        text = font_med.render(line, True, color)
        canvas.blit(text, text.get_rect(center=(SCREEN_W // 2, 130 + i * 32)))

    if not scores:
        empty = font_med.render("No runs recorded yet.", True, (180, 160, 130))
        canvas.blit(empty, empty.get_rect(center=(SCREEN_W // 2, 200)))

    hint = font_small.render("ENTER to return to menu   ESC to quit", True, (150, 130, 100))
    canvas.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H - 40)))
    present()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main():
    game_state = "menu"
    name_input = ""
    cursor_timer = 0
    cursor_on = True
    top_scores = load_scores()
    latest_entry = None
    score_saved = False

    level = 1
    platforms, spawn_slots, level_width, powerup_specs = build_level(level)
    current_theme = theme_for_level(level)
    player = Player(60, SCREEN_H - 100)
    enemies = []
    bullets, grenades, explosions, powerups = [], [], [], []
    wave_clear_timer = 0

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    toggle_fullscreen()
                    continue

                if game_state == "menu":
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_RETURN:
                        level = 1
                        platforms, spawn_slots, level_width, powerup_specs = build_level(level)
                        current_theme = theme_for_level(level)
                        player = Player(60, SCREEN_H - 100, name=(name_input.strip() or "TROOPER"))
                        enemies = spawn_wave(level, spawn_slots)
                        bullets, grenades, explosions = [], [], []
                        powerups = [Powerup(x, y, ptype) for (x, y, ptype) in powerup_specs]
                        score_saved = False
                        latest_entry = None
                        game_state = "playing"
                    elif event.key == pygame.K_BACKSPACE:
                        name_input = name_input[:-1]
                    else:
                        ch = event.unicode
                        if ch and ch.isprintable() and len(name_input) < MAX_NAME_LEN:
                            name_input += ch

                elif game_state == "playing":
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_1:
                        player.switch_weapon(0)
                    if event.key == pygame.K_2:
                        player.switch_weapon(1)
                    if event.key == pygame.K_3:
                        player.switch_weapon(2)

                elif game_state == "dead":
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_RETURN:
                        top_scores = load_scores()
                        game_state = "leaderboard"

                elif game_state == "leaderboard":
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_RETURN:
                        game_state = "menu"

            if event.type == pygame.MOUSEBUTTONDOWN and game_state == "playing":
                player.fire(bullets, grenades, enemies)

        # -------------------------------------------------------------
        if game_state == "menu":
            cursor_timer += 1
            if cursor_timer >= FPS // 2:
                cursor_timer = 0
                cursor_on = not cursor_on
            draw_menu(name_input, cursor_on, top_scores)

        elif game_state == "playing":
            keys = pygame.key.get_pressed()
            player.handle_input(keys, level_width)
            if keys[pygame.K_j]:
                player.fire(bullets, grenades, enemies)
            player.update(platforms, level_width)

            for e in enemies:
                if e.alive:
                    e.update(bullets)

            for b in bullets:
                b.update(level_width)
            for g in grenades:
                g.update(platforms, level_width)
                if g.exploded:
                    explosions.append(Explosion(g.rect.centerx, g.rect.centery))
                    for e in enemies:
                        if e.alive:
                            dist = math.hypot(e.rect.centerx - g.rect.centerx, e.rect.centery - g.rect.centery)
                            if dist <= Explosion.RADIUS:
                                e.take_hit(45)
                                if not e.alive:
                                    player.score += e.score_value
                    g.alive = False
            for ex in explosions:
                ex.update()

            for b in bullets:
                if not b.alive:
                    continue
                if b.from_player:
                    for e in enemies:
                        if e.alive and b.rect.colliderect(e.rect):
                            e.take_hit(b.dmg)
                            b.alive = False
                            if not e.alive:
                                player.score += e.score_value
                            break
                else:
                    if b.rect.colliderect(player.rect):
                        player.take_damage(b.dmg)
                        b.alive = False

            for pu in powerups:
                if pu.alive and player.rect.colliderect(pu.rect):
                    if pu.ptype == "armor":
                        player.health = min(player.max_health, player.health + 35)
                    else:
                        player.grenade_count += 2
                    pu.alive = False

            bullets = [b for b in bullets if b.alive]
            grenades = [g for g in grenades if g.alive]
            explosions = [ex for ex in explosions if ex.alive]
            enemies = [e for e in enemies if e.alive]
            powerups = [pu for pu in powerups if pu.alive]

            if player.health <= 0:
                game_state = "dead"

            if not enemies:
                game_state = "wave_clear"
                wave_clear_timer = FPS * 2

            camera_x = get_camera_x(player, level_width)
            draw_background(canvas, camera_x, current_theme)
            draw_platforms(canvas, platforms, camera_x, current_theme)
            for pu in powerups:
                pu.draw(canvas, camera_x)
            for e in enemies:
                e.draw(canvas, camera_x)
            for b in bullets:
                b.draw(canvas, camera_x)
            for g in grenades:
                g.draw(canvas, camera_x)
            for ex in explosions:
                ex.draw(canvas, camera_x)
            player.draw(canvas, camera_x)
            draw_ui(canvas, player, level, current_theme)
            present()

        elif game_state == "wave_clear":
            camera_x = get_camera_x(player, level_width)
            draw_background(canvas, camera_x, current_theme)
            draw_platforms(canvas, platforms, camera_x, current_theme)
            player.draw(canvas, camera_x)
            draw_ui(canvas, player, level, current_theme)
            msg = font_big.render(f"LEVEL {level} CLEARED", True, COL_UI_TEXT)
            canvas.blit(msg, msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2)))
            present()

            wave_clear_timer -= 1
            if wave_clear_timer <= 0:
                level += 1
                player.levels_cleared += 1
                platforms, spawn_slots, level_width, powerup_specs = build_level(level)
                current_theme = theme_for_level(level)
                player.grenade_count += 1
                player.rect.topleft = (60, SCREEN_H - 100)
                enemies = spawn_wave(level, spawn_slots)
                bullets, grenades, explosions = [], [], []
                powerups = [Powerup(x, y, ptype) for (x, y, ptype) in powerup_specs]
                game_state = "playing"

        elif game_state == "dead":
            if not score_saved:
                top_scores = save_score(player.name, player.score, level)
                latest_entry = next(
                    (e for e in top_scores
                     if e.get("name") == (player.name.strip() or "TROOPER")[:MAX_NAME_LEN]
                     and e.get("score") == player.score and e.get("level") == level),
                    None,
                )
                score_saved = True
            show_message(
                ["YOU HAVE FALLEN"],
                f"{player.name} - Reached Level {level}   Score: {player.score}   ENTER for leaderboard",
            )

        elif game_state == "leaderboard":
            draw_leaderboard(top_scores, latest_entry)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
