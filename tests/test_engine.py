import pytest
from src.engine.core import GameEngine

def test_game_engine_init():
    engine = GameEngine()
    assert engine.screen_size == (800, 600)
    assert engine.running == True
    assert engine.fps == 60 