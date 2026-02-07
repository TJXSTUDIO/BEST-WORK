import math
import random
import sys
from dataclasses import dataclass

import pygame

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
FPS = 60

PLAYER_SPEED = 240
PLAYER_RADIUS = 18
PLAYER_MAX_HEALTH = 100

BULLET_SPEED = 520
BULLET_LIFETIME = 0.9
BULLET_RADIUS = 4

ENEMY_SPEED = 120
ENEMY_RADIUS = 16
ENEMY_SPAWN_TIME = 1.2

COLOR_BG = (18, 18, 25)
COLOR_FLOOR = (28, 28, 35)
COLOR_PLAYER = (80, 200, 255)
COLOR_PLAYER_ACCENT = (245, 245, 255)
COLOR_ENEMY = (255, 90, 90)
COLOR_BULLET = (255, 215, 0)
COLOR_HUD = (230, 230, 230)
COLOR_HUD_ACCENT = (60, 200, 120)


@dataclass
class Bullet:
    position: pygame.Vector2
    velocity: pygame.Vector2
    ttl: float


@dataclass
class Enemy:
    position: pygame.Vector2
    health: int = 30


@dataclass
class Player:
    position: pygame.Vector2
    velocity: pygame.Vector2
    health: int
    facing: pygame.Vector2


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def create_player() -> Player:
    return Player(
        position=pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2),
        velocity=pygame.Vector2(0, 0),
        health=PLAYER_MAX_HEALTH,
        facing=pygame.Vector2(1, 0),
    )


def spawn_enemy(player_position: pygame.Vector2) -> Enemy:
    margin = 40
    side = random.choice(["top", "bottom", "left", "right"])
    if side == "top":
        position = pygame.Vector2(random.uniform(0, SCREEN_WIDTH), -margin)
    elif side == "bottom":
        position = pygame.Vector2(random.uniform(0, SCREEN_WIDTH), SCREEN_HEIGHT + margin)
    elif side == "left":
        position = pygame.Vector2(-margin, random.uniform(0, SCREEN_HEIGHT))
    else:
        position = pygame.Vector2(SCREEN_WIDTH + margin, random.uniform(0, SCREEN_HEIGHT))

    if position.distance_to(player_position) < 160:
        position += (position - player_position).normalize() * 160
    return Enemy(position=position)


def draw_grid(surface: pygame.Surface) -> None:
    surface.fill(COLOR_BG)
    grid_color = (35, 35, 45)
    cell = 40
    for x in range(0, SCREEN_WIDTH, cell):
        pygame.draw.line(surface, grid_color, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, cell):
        pygame.draw.line(surface, grid_color, (0, y), (SCREEN_WIDTH, y))


def draw_player(surface: pygame.Surface, player: Player) -> None:
    pygame.draw.circle(surface, COLOR_PLAYER, player.position, PLAYER_RADIUS)
    gun_tip = player.position + player.facing.normalize() * (PLAYER_RADIUS + 6)
    pygame.draw.circle(surface, COLOR_PLAYER_ACCENT, gun_tip, 5)


def draw_enemy(surface: pygame.Surface, enemy: Enemy) -> None:
    pygame.draw.circle(surface, COLOR_ENEMY, enemy.position, ENEMY_RADIUS)
    pygame.draw.circle(surface, (90, 20, 20), enemy.position, ENEMY_RADIUS, 2)


def draw_bullet(surface: pygame.Surface, bullet: Bullet) -> None:
    pygame.draw.circle(surface, COLOR_BULLET, bullet.position, BULLET_RADIUS)


def draw_hud(surface: pygame.Surface, player: Player, score: int, wave: int) -> None:
    pygame.draw.rect(surface, (40, 40, 45), (18, 18, 220, 24), border_radius=6)
    health_ratio = player.health / PLAYER_MAX_HEALTH
    pygame.draw.rect(surface, COLOR_HUD_ACCENT, (20, 20, int(216 * health_ratio), 20), border_radius=5)
    font = pygame.font.Font(None, 28)
    score_text = font.render(f"Score: {score}", True, COLOR_HUD)
    wave_text = font.render(f"Wave {wave}", True, COLOR_HUD)
    surface.blit(score_text, (18, 52))
    surface.blit(wave_text, (18, 78))


def handle_movement(keys: pygame.key.ScancodeWrapper) -> pygame.Vector2:
    direction = pygame.Vector2(0, 0)
    if keys[pygame.K_w]:
        direction.y -= 1
    if keys[pygame.K_s]:
        direction.y += 1
    if keys[pygame.K_a]:
        direction.x -= 1
    if keys[pygame.K_d]:
        direction.x += 1
    if direction.length_squared() > 0:
        direction = direction.normalize()
    return direction


def spawn_bullet(player: Player, target: pygame.Vector2) -> Bullet:
    direction = (target - player.position)
    if direction.length_squared() == 0:
        direction = player.facing
    direction = direction.normalize()
    player.facing = direction
    velocity = direction * BULLET_SPEED
    return Bullet(position=pygame.Vector2(player.position), velocity=velocity, ttl=BULLET_LIFETIME)


def update_player(player: Player, movement: pygame.Vector2, dt: float) -> None:
    player.velocity = movement * PLAYER_SPEED
    player.position += player.velocity * dt
    player.position.x = clamp(player.position.x, PLAYER_RADIUS, SCREEN_WIDTH - PLAYER_RADIUS)
    player.position.y = clamp(player.position.y, PLAYER_RADIUS, SCREEN_HEIGHT - PLAYER_RADIUS)


def update_enemies(enemies: list[Enemy], player: Player, dt: float) -> None:
    for enemy in enemies:
        to_player = (player.position - enemy.position)
        if to_player.length_squared() > 0:
            enemy.position += to_player.normalize() * ENEMY_SPEED * dt


def update_bullets(bullets: list[Bullet], dt: float) -> None:
    for bullet in bullets:
        bullet.position += bullet.velocity * dt
        bullet.ttl -= dt


def handle_collisions(bullets: list[Bullet], enemies: list[Enemy], player: Player) -> int:
    score_delta = 0
    for bullet in bullets[:]:
        for enemy in enemies[:]:
            if bullet.position.distance_to(enemy.position) <= ENEMY_RADIUS + BULLET_RADIUS:
                enemies.remove(enemy)
                if bullet in bullets:
                    bullets.remove(bullet)
                score_delta += 10
                break

    for enemy in enemies[:]:
        if enemy.position.distance_to(player.position) <= ENEMY_RADIUS + PLAYER_RADIUS:
            enemies.remove(enemy)
            player.health -= 12

    return score_delta


def show_game_over(surface: pygame.Surface, score: int) -> None:
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((10, 10, 15, 220))
    surface.blit(overlay, (0, 0))

    font_big = pygame.font.Font(None, 72)
    font_small = pygame.font.Font(None, 32)
    title = font_big.render("GAME OVER", True, COLOR_HUD)
    prompt = font_small.render("Press R to restart", True, COLOR_HUD)
    score_text = font_small.render(f"Final Score: {score}", True, COLOR_HUD)

    surface.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40)))
    surface.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 12)))
    surface.blit(prompt, prompt.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 56)))


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Third-Person Shooter")
    clock = pygame.time.Clock()

    player = create_player()
    bullets: list[Bullet] = []
    enemies: list[Enemy] = []
    score = 0
    wave = 1
    spawn_timer = 0.0
    shooting = False
    game_over = False

    while True:
        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                shooting = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                shooting = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r and game_over:
                player = create_player()
                bullets.clear()
                enemies.clear()
                score = 0
                wave = 1
                spawn_timer = 0.0
                shooting = False
                game_over = False

        if not game_over:
            keys = pygame.key.get_pressed()
            movement = handle_movement(keys)
            update_player(player, movement, dt)

            mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
            if mouse_pos.distance_to(player.position) > 0:
                player.facing = (mouse_pos - player.position).normalize()

            spawn_timer -= dt
            spawn_limit = max(0.35, ENEMY_SPAWN_TIME - wave * 0.08)
            if spawn_timer <= 0:
                enemies.append(spawn_enemy(player.position))
                spawn_timer = spawn_limit

            if shooting and len(bullets) < 6:
                bullets.append(spawn_bullet(player, mouse_pos))

            update_bullets(bullets, dt)
            bullets[:] = [bullet for bullet in bullets if bullet.ttl > 0]
            update_enemies(enemies, player, dt)

            score += handle_collisions(bullets, enemies, player)

            if score // 100 + 1 > wave:
                wave += 1

            if player.health <= 0:
                player.health = 0
                game_over = True

        draw_grid(screen)
        pygame.draw.rect(screen, COLOR_FLOOR, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 4)

        for bullet in bullets:
            draw_bullet(screen, bullet)
        for enemy in enemies:
            draw_enemy(screen, enemy)
        draw_player(screen, player)
        draw_hud(screen, player, score, wave)

        if game_over:
            show_game_over(screen, score)

        pygame.display.flip()


if __name__ == "__main__":
    main()
