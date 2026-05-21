import unittest
import os
import sys
import tempfile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import save_json, load_json
from entities.player import Player
from settings import PLAYER_SIZE


class TestBasicGameFunctions(unittest.TestCase):

    def test_json_save_and_load(self):
        data = {
            "score": 100,
            "inventory": ["Fuse A", "Fuse B"]
        }

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            path = tmp.name

        save_json(path, data)
        loaded = load_json(path, {})

        os.remove(path)

        self.assertEqual(loaded["score"], 100)
        self.assertIn("Fuse A", loaded["inventory"])

    def test_player_hitbox_exists(self):
        player = Player(100, 100, PLAYER_SIZE)
        hitbox = player.get_hitbox()

        self.assertTrue(hitbox.width > 0)
        self.assertTrue(hitbox.height > 0)

    def test_player_animation_changes(self):
        player = Player(100, 100, PLAYER_SIZE)
        player.update_animation(True, 0.2)

        self.assertIn(player.anim_index, [0, 1])


if __name__ == "__main__":
    unittest.main()