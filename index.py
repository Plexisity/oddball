import os
import arcade
from player import Player

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN_TITLE = "Oddball"

class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        arcade.set_background_color(arcade.color.WHITE)

        # Sprites
        self.sprite_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()

        # Player
        self.player = Player(os.path.join("assets/player/Idle.png"), 1)
        self.player.center_x = SCREEN_WIDTH // 2
        self.player.center_y = 500
        self.sprite_list.append(self.player)

        # Ground
        ground = arcade.SpriteSolidColor(SCREEN_WIDTH, 100, arcade.color.DARK_GREEN)
        ground.center_x = SCREEN_WIDTH // 2
        ground.center_y = 50
        self.wall_list.append(ground)

        # Physics
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player,
            walls=self.wall_list,
            gravity_constant=1.0
        )

    def on_draw(self):
        self.clear()
        self.wall_list.draw()
        self.sprite_list.draw()

    def on_update(self, delta_time: float):
        self.player.update_movement()
        self.physics_engine.update()
        self.player.update_animation(delta_time)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP and self.physics_engine.can_jump():
            self.player.YVelocity = self.player.jump_speed
        elif key == arcade.key.LEFT:
            self.player.left_pressed = True
        elif key == arcade.key.RIGHT:
            self.player.right_pressed = True

    def on_key_release(self, key, modifiers):


        if key == arcade.key.LEFT:
            self.player.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.player.right_pressed = False


# ----------------------
# MAIN
# ----------------------
def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game = GameView()
    window.show_view(game)
    arcade.run()


if __name__ == "__main__":
    main()