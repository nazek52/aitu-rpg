import math
import pygame


class Note:
    def __init__(self, title, text, x, y, image):
        self.title = title
        self.text = text
        self.rect = image.get_rect(topleft=(x, y))
        self.image = image
        self.read = False
        self.float_seed = x * 0.02

    def distance_to(self, rect):
        return math.hypot(self.rect.centerx - rect.centerx, self.rect.centery - rect.centery)

    def draw(self, screen, camera_x, camera_y):
        time = pygame.time.get_ticks() * 0.005
        float_y = math.sin(time + self.float_seed) * 5
        x = self.rect.x - camera_x
        y = self.rect.y + float_y - camera_y
        glow_color = (120, 190, 255, 35) if not self.read else (150, 150, 150, 18)
        glow = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(glow, glow_color, (30, 30), 25)
        screen.blit(glow, (x - 13, y - 13))
        screen.blit(self.image, (x, y))