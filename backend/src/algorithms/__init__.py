"""
Algorithms package for the ride dispatch simulation system
Contains dispatch, acceptance, and movement logic
"""
from .dispatch import (
    find_eligible_drivers,
    prioritize_drivers,
    dispatch_ride,
    attempt_fallback_dispatch,
    batch_dispatch
)

from .acceptance import (
    should_accept_ride,
    process_driver_response,
    auto_process_acceptance,
    check_driver_workload,
    calculate_acceptance_probability
)

from .movement import (
    Direction,
    move_driver_randomly,
    move_driver_toward_target,
    update_driver_search_radius,
    process_driver_movement,
    complete_ride,
    process_all_driver_movements,
    get_nearby_drivers
)

__all__ = [
    # Dispatch
    'find_eligible_drivers',
    'prioritize_drivers',
    'dispatch_ride',
    'attempt_fallback_dispatch',
    'batch_dispatch',
    # Acceptance
    'should_accept_ride',
    'process_driver_response',
    'auto_process_acceptance',
    'check_driver_workload',
    'calculate_acceptance_probability',
    # Movement
    'Direction',
    'move_driver_randomly',
    'move_driver_toward_target',
    'update_driver_search_radius',
    'process_driver_movement',
    'complete_ride',
    'process_all_driver_movements',
    'get_nearby_drivers'
]