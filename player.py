import os
import arcade


class Player(arcade.Sprite):
    def __init__(self, asset_path: str, scale: float = 1.0):
        super().__init__(asset_path, scale)

        # Horizontal movement constants
        self.acceleration = 0.9
        self.max_speed = 8.0
        self.friction = 0.80
        self.jump_speed = 20.0

        # Key press tracking
        self.left_pressed = False
        self.right_pressed = False

        # Animation textures (right + mirrored left)
        idle_right = arcade.load_texture(os.path.join("assets/player", "Idle.png"))
        self.idle_textures = [idle_right, idle_right.flip_left_right()]

        walk_right = [
            arcade.load_texture(os.path.join("assets/player", f"Walk{i}.png"))
            for i in range(1, 4)
        ]
        self.walk_textures = [
            walk_right,
            [texture.flip_left_right() for texture in walk_right],
        ]

        up_right = arcade.load_texture(os.path.join("assets/player", "Up.png"))
        down_right = arcade.load_texture(os.path.join("assets/player", "Down.png"))
        self.up_textures = [up_right, up_right.flip_left_right()]
        self.down_textures = [down_right, down_right.flip_left_right()]

        # Animation state
        self.animation_index = 0
        self.animation_timer = 0.0
        self.facing = 0  # 0=right, 1=left
        self.texture = self.idle_textures[self.facing]

    def update_movement(self):
        """Update only horizontal movement. Vertical movement is handled by physics engine."""
        if self.right_pressed and not self.left_pressed:
            self.change_x += self.acceleration
            self.facing = 0
        elif self.left_pressed and not self.right_pressed:
            self.change_x -= self.acceleration
            self.facing = 1
        else:
            self.change_x *= self.friction

        # Clamp horizontal speed and remove tiny drift
        self.change_x = max(-self.max_speed, min(self.change_x, self.max_speed))
        if abs(self.change_x) < 0.05:
            self.change_x = 0

    def update_animation(self, delta_time: float = 1 / 60):
        if self.change_y > 1:
            self.texture = self.up_textures[self.facing]
            return

        if self.change_y < -1:
            self.texture = self.down_textures[self.facing]
            return

        if abs(self.change_x) > 0.2:
            self.animation_timer += delta_time
            if self.animation_timer > 0.08:
                self.animation_index = (self.animation_index + 1) % len(self.walk_textures[0])
                self.animation_timer = 0
            self.texture = self.walk_textures[self.facing][self.animation_index]
        else:
            self.texture = self.idle_textures[self.facing]
