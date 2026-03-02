import arcade
import os

class Player(arcade.Sprite):
    def __init__(self, asset_path: str, scale: float = 1.0):
        super().__init__(asset_path, scale)

        # Movement velocity
        self.XVelocity = 0
        self.YVelocity = 0

        # Movement constants
        self.acceleration = 1.0
        self.max_speed = 4.0
        self.friction = 0.85
        self.jump_speed = 20.0

        # Key press tracking
        self.left_pressed = False
        self.right_pressed = False

        # Animation textures
        self.idle_texture = arcade.load_texture(os.path.join("assets/player", "Idle.png"))
        self.walk_textures = [
            arcade.load_texture(os.path.join("assets/player", f"Walk{i}.png"))
            for i in range(1, 4)
        ]
        self.up_texture = arcade.load_texture(os.path.join("assets/player", "Up.png"))
        self.down_texture = arcade.load_texture(os.path.join("assets/player", "Down.png"))

        # Animation state
        self.animation_index = 0
        self.animation_timer = 0
        self.texture = self.idle_texture

    def update_movement(self):
        # Horizontal movement with acceleration + max speed
        if self.right_pressed and abs(self.XVelocity) < self.max_speed:
            self.XVelocity += self.acceleration
        if self.left_pressed and abs(self.XVelocity) < self.max_speed:
            self.XVelocity -= self.acceleration

        # Apply friction
        self.XVelocity *= self.friction

        # Update position
        self.center_x += self.XVelocity
        self.center_y += self.YVelocity

    def update_animation(self, delta_time: float = 1/60):
        # Vertical velocity determines Up/Down animation
        if self.YVelocity > 3:
            self.texture = self.up_texture
        elif self.YVelocity < 0:
            self.texture = self.down_texture
        else:
            # Horizontal movement -> walk animation
            if abs(self.XVelocity) > 0.1:
                self.animation_timer += delta_time
                if self.animation_timer > 0.05:
                    self.animation_index = (self.animation_index + 1) % len(self.walk_textures)
                    self.texture = self.walk_textures[self.animation_index]
                    self.animation_timer = 0
            else:
                self.texture = self.idle_texture