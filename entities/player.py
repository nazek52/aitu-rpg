import pygame


class Player:
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size[0], size[1])
        self.direction = "down"
        self.hidden = False

        self.anim_index = 0
        self.anim_timer = 0

    def get_hitbox(self):
        return pygame.Rect(
            self.rect.x + 8,
            self.rect.y + self.rect.height - 22,
            self.rect.width - 16,
            18
        )

    def update_animation(self, moving, dt):
        if moving:
            self.anim_timer += dt

            if self.anim_timer >= 0.16:
                self.anim_timer = 0
                self.anim_index = 1 - self.anim_index
        else:
            self.anim_index = 0

    def draw(self, screen, camera_x, camera_y, player_images, small_font):
        if self.hidden:
            text = small_font.render("HIDDEN", True, (150, 210, 255))
            screen.blit(text, (self.rect.x - camera_x, self.rect.y - camera_y - 25))
            return

        image = player_images[self.direction][self.anim_index]
        screen.blit(image, (self.rect.x - camera_x, self.rect.y - camera_y))