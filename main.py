import pygame
import math
from PIL import Image

from core.game import Game
from settings import SCREEN_W, SCREEN_H, FPS


class GifPlayer:
    def __init__(self, gif_path, size):
        self.frames = []
        self.frame_index = 0
        self.last_update = 0
        self.frame_delay = 80

        gif = Image.open(gif_path)

        try:
            while True:
                frame = gif.convert("RGBA")
                frame = frame.resize(size)

                py_image = pygame.image.fromstring(
                    frame.tobytes(),
                    frame.size,
                    frame.mode
                )

                self.frames.append(py_image)
                gif.seek(gif.tell() + 1)

        except EOFError:
            pass

    def update(self):
        now = pygame.time.get_ticks()

        if now - self.last_update > self.frame_delay:
            self.last_update = now
            self.frame_index = (self.frame_index + 1) % len(self.frames)

    def draw(self, screen):
        screen.blit(self.frames[self.frame_index], (0, 0))


def main():
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Project: Nexus")

    clock = pygame.time.Clock()

    # GIF-заставка
    menu_gif = GifPlayer(
        "assets/videos/project_nexus_breathing.gif",
        (SCREEN_W, SCREEN_H)
    )

    # Музыка меню
    try:
        pygame.mixer.music.load("assets/sounds/menu_music.mp3")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
    except pygame.error:
        print("menu_music.mp3 не найден")

    in_menu = True
    game = None
    running = True

    while running:
        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                if game:
                    game.save_score()
                running = False

            elif event.type == pygame.KEYDOWN:

                if in_menu:
                    if event.key == pygame.K_RETURN:
                        pygame.mixer.music.stop()
                        game = Game(screen)
                        in_menu = False

                    elif event.key == pygame.K_ESCAPE:
                        running = False

                else:
                    if event.key == pygame.K_ESCAPE:
                        game.save_score()
                        running = False
                    else:
                        game.handle_keydown(event.key)

        if in_menu:
            menu_gif.update()
            menu_gif.draw(screen)

            time_now = pygame.time.get_ticks()

            alpha = 120 + abs(int(135 * math.sin(time_now * 0.006)))

            font = pygame.font.Font(None, 54)

            text_value = "PRESS ENTER TO START"

            shadow = font.render(text_value, True, (25, 0, 0))
            shadow_rect = shadow.get_rect(
                center=(SCREEN_W // 2 + 4, SCREEN_H - 58)
            )

            text = font.render(text_value, True, (150, 0, 0))
            text = text.convert_alpha()
            text.set_alpha(alpha)

            shake_x = int(math.sin(time_now * 0.04) * 2)
            shake_y = int(math.sin(time_now * 0.03) * 1)

            text_rect = text.get_rect(
                center=(SCREEN_W // 2 + shake_x, SCREEN_H - 62 + shake_y)
            )

            screen.blit(shadow, shadow_rect)
            screen.blit(text, text_rect)

        else:
            game.update(dt)
            game.draw()

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()