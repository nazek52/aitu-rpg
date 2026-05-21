import json
import os
import pygame

ASSET_DIR = "assets"


def asset(filename):
    return os.path.join(ASSET_DIR, filename)


def load_image(filename, size=None, alpha=True):
    path = asset(filename)

    try:
        image = pygame.image.load(path)

        if alpha:
            image = image.convert_alpha()
        else:
            image = image.convert()

        if size:
            image = pygame.transform.smoothscale(image, size)

        return image

    except Exception as e:
        print(f"[IMAGE ERROR] Cannot load: {path}")
        print(e)

        fallback = pygame.Surface(size if size else (50, 50), pygame.SRCALPHA)
        fallback.fill((255, 0, 255, 180))
        return fallback


def load_json(path, default):
    if not os.path.exists(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception as e:
        print(f"[JSON ERROR] Cannot load {path}: {e}")
        return default


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    except Exception as e:
        print(f"[JSON ERROR] Cannot save {path}: {e}")