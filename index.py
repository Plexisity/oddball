import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import arcade
from PIL import Image

from player import Player

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN_TITLE = "Oddball"

GRAVITY = 1.0

# Level color keys
BLACK = (0, 0, 0)      # Bounce surface (fling up)
RED = (255, 0, 0)      # Send player back one level
GREEN = (0, 255, 0)    # Send player forward one level
WHITE = (255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)

# Generic solid colors that stay visible and collide
VISIBLE_SOLID_COLORS = {
    (40, 40, 40),
    (128, 128, 128),
    (255, 255, 0),
    (0, 0, 255),
    (255, 165, 0),
}


@dataclass(frozen=True)
class RectRun:
    x: int
    y: int
    width: int
    height: int
    color: Tuple[int, int, int]


class GameView(arcade.View):
    # Defensive defaults in case on_draw is called before __init__ completes
    level_texture: Optional[arcade.Texture] = None
    level_size: Tuple[int, int] = (SCREEN_WIDTH, SCREEN_HEIGHT)

    def __init__(self):
        super().__init__()
        arcade.set_background_color(arcade.color.WHITE)

        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList(use_spatial_hash=True)
        self.bounce_list = arcade.SpriteList(use_spatial_hash=True)
        self.hazard_list = arcade.SpriteList(use_spatial_hash=True)
        self.goal_list = arcade.SpriteList(use_spatial_hash=True)

        self.player = Player(os.path.join("assets/player/Idle.png"), 1)
        self.player_list.append(self.player)

        self.level_paths = self._discover_levels()
        self.level_index = 0
        self.spawn_point = (140, 220)

        self.physics_engine = None
        self._load_level(self.level_index)

    def _discover_levels(self) -> List[str]:
        levels_dir = os.path.join("assets", "levels")
        if not os.path.isdir(levels_dir):
            return []

        return sorted(
            os.path.join(levels_dir, path)
            for path in os.listdir(levels_dir)
            if path.lower().endswith(".png")
        )

    def _rgb(self, pixel: Tuple[int, ...]) -> Tuple[int, int, int]:
        if len(pixel) >= 3:
            return pixel[0], pixel[1], pixel[2]
        return pixel[0], pixel[0], pixel[0]

    def _is_empty(self, pixel: Tuple[int, ...]) -> bool:
        if len(pixel) == 4 and pixel[3] == 0:
            return True
        rgb = self._rgb(pixel)
        return rgb == WHITE

    def _build_merged_rectangles(self, image: Image.Image) -> Dict[str, List[RectRun]]:
        """
        Convert per-pixel mask image into merged rectangles.
        This is much faster than creating one sprite per pixel.
        """
        img = image.convert("RGBA")
        pixels = img.load()
        width, height = img.size

        by_row: Dict[int, List[Tuple[int, int, str, Tuple[int, int, int]]]] = defaultdict(list)

        for y in range(height):
            x = 0
            while x < width:
                px = pixels[x, y]
                if self._is_empty(px):
                    x += 1
                    continue

                rgb = self._rgb(px)
                block_type = "solid"
                if rgb == BLACK:
                    block_type = "bounce"
                elif rgb == RED:
                    block_type = "hazard"
                elif rgb == GREEN:
                    block_type = "goal"

                x_start = x
                x += 1
                while x < width:
                    nxt = pixels[x, y]
                    if self._is_empty(nxt):
                        break
                    nxt_rgb = self._rgb(nxt)
                    nxt_type = "solid"
                    if nxt_rgb == BLACK:
                        nxt_type = "bounce"
                    elif nxt_rgb == RED:
                        nxt_type = "hazard"
                    elif nxt_rgb == GREEN:
                        nxt_type = "goal"
                    if nxt_type != block_type or nxt_rgb != rgb:
                        break
                    x += 1

                by_row[y].append((x_start, x - x_start, block_type, rgb))

        merged: Dict[str, List[RectRun]] = {"solid": [], "bounce": [], "hazard": [], "goal": []}
        active: Dict[Tuple[int, int, str, Tuple[int, int, int]], RectRun] = {}

        for y in range(height):
            current_keys = set()
            for run_x, run_w, run_type, run_color in by_row[y]:
                key = (run_x, run_w, run_type, run_color)
                current_keys.add(key)
                if key in active:
                    rect = active[key]
                    active[key] = RectRun(rect.x, rect.y, rect.width, rect.height + 1, rect.color)
                else:
                    active[key] = RectRun(run_x, y, run_w, 1, run_color)

            done_keys = [k for k in active.keys() if k not in current_keys]
            for key in done_keys:
                run_x, _run_w, run_type, _run_color = key
                rect = active.pop(key)
                merged[run_type].append(rect)

        for key in list(active.keys()):
            run_type = key[2]
            merged[run_type].append(active.pop(key))

        return merged

    def _sprite_from_rect(self, rect: RectRun, world_height: int, color: Tuple[int, int, int]) -> arcade.Sprite:
        sprite = arcade.SpriteSolidColor(rect.width, rect.height, color)
        sprite.center_x = rect.x + rect.width / 2
        sprite.center_y = world_height - (rect.y + rect.height / 2)
        return sprite

    def _add_default_level(self):
        self.wall_list.clear()
        self.bounce_list.clear()
        self.hazard_list.clear()
        self.goal_list.clear()

        ground = arcade.SpriteSolidColor(SCREEN_WIDTH, 120, arcade.color.DARK_GREEN)
        ground.center_x = SCREEN_WIDTH // 2
        ground.center_y = 60
        self.wall_list.append(ground)

        goal = arcade.SpriteSolidColor(80, 200, arcade.color.APPLE_GREEN)
        goal.center_x = SCREEN_WIDTH - 100
        goal.center_y = 220
        self.goal_list.append(goal)

        self.spawn_point = (140, 220)

    def _load_level(self, index: int):
        self.wall_list.clear()
        self.bounce_list.clear()
        self.hazard_list.clear()
        self.goal_list.clear()

        if not self.level_paths:
            self._add_default_level()
        else:
            level_path = self.level_paths[index]
            image = Image.open(level_path)
            world_width, world_height = image.size
            self.window.set_size(world_width, world_height)

            self.spawn_point = (140, 220)

            merged = self._build_merged_rectangles(image)

            for rect in merged["bounce"]:
                bounce = self._sprite_from_rect(rect, world_height, BLACK)
                self.wall_list.append(bounce)
                self.bounce_list.append(bounce)

            for rect in merged["solid"]:
                base_color = rect.color if rect.color in VISIBLE_SOLID_COLORS else (90, 90, 90)
                self.wall_list.append(self._sprite_from_rect(rect, world_height, base_color))

            for rect in merged["hazard"]:
                self.hazard_list.append(self._sprite_from_rect(rect, world_height, RED))

            for rect in merged["goal"]:
                self.goal_list.append(self._sprite_from_rect(rect, world_height, GREEN))

        self.player.center_x, self.player.center_y = self.spawn_point
        self.player.change_x = 0
        self.player.change_y = 0

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player,
            walls=self.wall_list,
            gravity_constant=GRAVITY,
        )

    def _respawn_player(self):
        self.player.center_x, self.player.center_y = self.spawn_point
        self.player.change_x = 0
        self.player.change_y = 0

    def on_draw(self):
        self.clear()

        if self.level_texture is not None:
            width, height = self.level_size
            arcade.draw_lrwh_rectangle_textured(0, 0, width, height, self.level_texture)

        self.wall_list.draw()
        self.bounce_list.draw()
        self.hazard_list.draw()
        self.goal_list.draw()
        self.player_list.draw()

    def on_update(self, delta_time: float):
        self.player.update_movement()
        self.physics_engine.update()
        self.player.update_animation(delta_time)

        if arcade.check_for_collision_with_list(self.player, self.bounce_list):
            self.player.change_y = max(self.player.change_y, self.player.jump_speed * 1.2)

        if arcade.check_for_collision_with_list(self.player, self.hazard_list) and self.level_paths:
            self.level_index = max(0, self.level_index - 1)
            self._load_level(self.level_index)
            return

        if arcade.check_for_collision_with_list(self.player, self.goal_list) and self.level_paths:
            self.level_index = min(len(self.level_paths) - 1, self.level_index + 1)
            self._load_level(self.level_index)

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.UP, arcade.key.SPACE, arcade.key.W) and self.physics_engine.can_jump():
            self.player.change_y = self.player.jump_speed
        elif key in (arcade.key.LEFT, arcade.key.A):
            self.player.left_pressed = True
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.player.right_pressed = True

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.A):
            self.player.left_pressed = False
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.player.right_pressed = False


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=True)
    game = GameView()
    window.show_view(game)
    arcade.run()


if __name__ == "__main__":
    main()
