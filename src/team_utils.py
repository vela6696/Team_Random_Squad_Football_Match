"""Utility wrappers around team_select_optimized_lib for PyQt GUI.

This module re-exports core functions and constants from
``team_select_optimized_lib`` so that the PyQt GUI does not import the
original module directly. Any adjustments needed for the GUI can be
implemented here without modifying the original library.
"""
from pathlib import Path
import team_select_optimized_lib as _base

# Paths and constants
CSV_FILE = _base.CSV_FILE
CSV_PATH = Path(_base.__file__).with_name(CSV_FILE)

TEAM_COUNT = _base.TEAM_COUNT
NAME_KEY = _base.NAME_KEY
TIER_KEY = _base.TIER_KEY
POSITION_KEY = _base.POSITION_KEY
GK_LABEL = _base.GK_LABEL

# Configuration helpers

def get_tier_threshold() -> float:
    """Return the current low-tier threshold."""
    return _base.TIER_THRESHOLD_LOW


def set_tier_threshold(value: float) -> None:
    """Update the low-tier threshold used in team balancing."""
    _base.TIER_THRESHOLD_LOW = value

# Re-exported functions
read_players_from_csv = _base.read_players_from_csv
run_team_assignment = _base.run_team_assignment
add_new_player_to_csv = _base.add_new_player_to_csv
