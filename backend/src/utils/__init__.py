"""
Utilities package for the ride dispatch simulation system
"""
from .geometry import (
    manhattan_distance,
    is_within_radius,
    validate_coordinates,
    clamp_to_grid,
    calculate_eta,
    find_points_within_radius
)

__all__ = [
    'manhattan_distance',
    'is_within_radius',
    'validate_coordinates',
    'clamp_to_grid',
    'calculate_eta',
    'find_points_within_radius'
]