import pygame


class Door:
    def __init__(self, name, x, y, w, h, requirement=None):
        self.name = name
        self.rect = pygame.Rect(x, y, w, h)
        self.requirement = requirement
        self.opened = False

    def can_open(self, tasks, inventory, trunk):
        if self.requirement is None:
            return True
        return self.requirement(tasks, inventory, trunk)

    def try_open(self, tasks, inventory, trunk):
        if self.can_open(tasks, inventory, trunk):
            self.opened = True
            return True
        return False

    def blocks(self):
        return not self.opened

    def draw(self, screen, camera_x, camera_y):
        color = (40, 180, 90) if self.opened else (180, 35, 45)

        r = pygame.Rect(
            self.rect.x - camera_x,
            self.rect.y - camera_y,
            self.rect.w,
            self.rect.h
        )

        pygame.draw.rect(screen, color, r, 2)