"""Utility wrappers around ``team_select_optimized_lib`` for PyQt GUI.

This module re-exports core functions and constants from
``team_select_optimized_lib`` so that the PyQt GUI does not import the
original module directly. Any adjustments needed for the GUI can be
implemented here without modifying the original library.

The packaged executable built with PyInstaller runs from a temporary
directory, so relying on ``__file__`` to locate ``players.csv`` fails. We
need to resolve the CSV path differently when frozen into an executable
to keep the GUI working after compilation.
"""
from pathlib import Path
import sys
import team_select_optimized_lib as _base

# Paths and constants
CSV_FILE = _base.CSV_FILE


def _resolve_csv_path() -> Path:
    """Return path to ``players.csv`` for both source and packaged runs."""
    # When frozen by PyInstaller, ``sys.argv[0]`` points to the executable
    # location. Otherwise fall back to the location of the library module.
    if getattr(sys, "frozen", False):
        return Path(sys.argv[0]).resolve().parent / CSV_FILE
    return Path(_base.__file__).with_name(CSV_FILE)


CSV_PATH = _resolve_csv_path()

TEAM_COUNT = _base.TEAM_COUNT
NAME_KEY = _base.NAME_KEY
TIER_KEY = _base.TIER_KEY
POSITION_KEY = _base.POSITION_KEY
STRENGTH_KEY = _base.STRENGTH_KEY
GK_LABEL = _base.GK_LABEL

# Configuration helpers

def get_tier_threshold() -> float:
    """Return the current low-tier threshold."""
    return _base.TIER_THRESHOLD_LOW


def set_tier_threshold(value: float) -> None:
    """Update the low-tier threshold used in team balancing."""
    if value >= _base.TIER_THRESHOLD_HIGH:
        raise ValueError("Tier threshold must be lower than carrier threshold.")
    _base.TIER_THRESHOLD_LOW = value


def get_carrier_threshold() -> float:
    """Return the current carrier (strong) threshold."""
    return _base.TIER_THRESHOLD_HIGH


def set_carrier_threshold(value: float) -> None:
    """Update the high-tier threshold used to tag strong players."""
    if value <= _base.TIER_THRESHOLD_LOW:
        raise ValueError("Carrier threshold must be greater than tier threshold.")
    _base.TIER_THRESHOLD_HIGH = value

# Re-exported functions
read_players_from_csv = _base.read_players_from_csv
run_team_assignment = _base.run_team_assignment
add_new_player_to_csv = _base.add_new_player_to_csv
