#!/usr/bin/env python
#!coding:utf-8
import pytest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from client.playingrules import *

@pytest.mark.parametrize('user_input, expect', [
    [[15,15,15,15], (CardType.normal_bomb, 15)],
    [[16,16,16,16], (CardType.black_joker_bomb, 16)],
    [[17,17,17,17], (CardType.red_joker_bomb, 17)],
    [[8,10,11,16,17], (CardType.straight, 12)],
    [[3,3,4,16], (CardType.straight_pairs, 4)],
    [[3,3,3,4,16,16], (CardType.straight_triples, 4)],
    [[5,5,6,6,8,9,9,9,16,17], (CardType.flight, 9)],
    [[17], (CardType.single, 17)],
    [[15,17], (CardType.pair, 15)],
    [[15,15,17], (CardType.triple, 15)],
    [[4,5,5,5,16], (CardType.triple_pair, 5)],
    [[4,4,5,5,5], (CardType.triple_pair, 5)],
    [[4,4,4,4,17], (CardType.normal_bomb, 4)],
    [[9,9,10,10,11,11,11,12,12,12], (CardType.flight,12)],
    [[8,8,8,17,17], (CardType.normal_bomb, 8)],
])
def test_judge_and_transform_cards(user_input, expect):
    assert judge_and_transform_cards(sorted(user_input, reverse=True)) == expect

@pytest.mark.parametrize('user_input, user_card, last_played_cards, expect', [
    [[4,5,6,7,8,9,13,10,16,17], [4,5,6,7,8,9,9,9,9,9,10,13,14,14,14,15,16,17], None, (False, 25)],
    [[15,15,15,15,15], None, [4,4,4,4,17], (True, 0)],
])
def test_if_input_legal(user_input, user_card, last_played_cards, expect):
    assert if_input_legal(user_input, user_card, last_played_cards) == expect
