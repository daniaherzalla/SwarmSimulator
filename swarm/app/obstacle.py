"""Obstacle class."""
import pygame
import numpy as np
from . import params
from . import assets


class Obstacle(pygame.sprite.Sprite):
    """A circular obstacle for drones to avoid."""

    def __init__(self, pos=None, radius=None):
        super().__init__()
        self.radius = np.random.randint(5, 50)
        self.density = np.random.uniform(0.1, 1)
        self.image, self.rect = assets.image_with_rect('obstacle-circle.png')
        self.image = pygame.transform.smoothscale(
            self.image, (2 * self.radius, 2 * self.radius))
        if pos is not None:
            self.pos = pos
        else:
            # Generate a random position for the obstacle
            x = np.random.randint(0, params.SCREEN_WIDTH - self.radius)
            y = np.random.randint(0, params.SCREEN_HEIGHT - self.radius)
            self.pos = np.array([x, y])
        self.rect = self.image.get_rect(center=self.pos)

    def display(self, screen):
        screen.blit(self.image, self.rect)
