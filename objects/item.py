import math
import pygame


class GameObject:
    def __init__(self, name, x, y, image):
        self.name = name
        self.x = x
        self.y = y
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, screen, camera_x, camera_y):
        screen.blit(self.image, (self.x - camera_x, self.y - camera_y))


class Collectible(GameObject):
    def __init__(self, name, x, y, image, required=True):
        super().__init__(name, x, y, image)
        self.collected = False
        self.required = required

    def draw(self, screen, camera_x, camera_y):
        if self.collected:
            return

        time = pygame.time.get_ticks()
        float_y = math.sin(time * 0.006 + self.x) * 7

        glow = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.circle(glow, (120, 220, 255, 35), (35, 35), 30)

        screen.blit(glow, (self.x - camera_x - 14, self.y - camera_y - 14 + float_y))
        screen.blit(self.image, (self.x - camera_x, self.y - camera_y + float_y))


class Note(GameObject):
    def __init__(self, title, text, x, y, image):
        super().__init__(title, x, y, image)
        self.title = title
        self.text = text
        self.read = False

    def draw(self, screen, camera_x, camera_y):
        time = pygame.time.get_ticks()
        float_y = math.sin(time * 0.005 + self.x) * 5

        screen.blit(self.image, (self.x - camera_x, self.y - camera_y + float_y))