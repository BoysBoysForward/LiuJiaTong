import sys
import os
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from card import Card, Suits
import utils

class TestUtils(unittest.TestCase):
    def test_strs_to_ints(self):
        strs = ['3', '4', '5', '6', '7']
        expected = [3, 4, 5, 6, 7]
        self.assertEqual(utils.strs_to_ints(strs), expected)

    def test_draw_cards(self):
        cards = [Card(Suits.heart, 3), Card(Suits.diamond, 4), Card(Suits.club, 5), Card(Suits.spade, 6), Card(Suits.heart, 7)]
        targets = ['3', '4', '5', '6', '7']
        self.assertEqual(utils.draw_cards(cards, targets), cards)

if __name__ == '__main__':
    unittest.main()