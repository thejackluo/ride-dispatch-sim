"""
Dispatch algorithm for the ride dispatch simulation system
Finds and prioritizes drivers for ride requests
"""
from typing import List, Optional, Tuple, Dict
import logging

from ..models import Driver, RideRequest, DriverStatus, RideStatus
from ..utils.geometry import manhattan_distance, is_within_radius
from ..state import SimulationState

logger = logging.getLogger(__name__)


def find_eligible_drivers(ride: RideRequest, drivers: List[Driver],
                         search_radius: Optional[int] = None) -> List[Driver]:
    """
    Find all drivers eligible for a ride request
    Filters by availability and distance from pickup location

    Args:
        ride: The ride request to find drivers for
        drivers: List of all drivers to consider
        search_radius: Optional override for search radius (if None, uses ride's pickup location)

    Returns:
        List of eligible drivers within search radius of pickup

    Note:
        Uses circular search pattern with Manhattan distance
        Only considers drivers with AVAILABLE status
    """
    eligible = []

    for driver in drivers:
        # Check if driver is available
        if driver.status != DriverStatus.AVAILABLE:
            continue

        # Check if driver has already rejected this ride
        if driver.id in ride.rejected_driver_ids:
            continue

        # Check if pickup is within driver's search radius
        if is_within_radius(driver.x, driver.y,
                           ride.pickup_x, ride.pickup_y,
                           driver.search_radius):
            eligible.append(driver)

    return eligible


def prioritize_drivers(eligible_drivers: List[Driver],
                      ride: RideRequest,
                      fairness_weight: float = 1.0) -> List[Driver]:
    """
    Prioritize eligible drivers based on fairness and efficiency

    Args:
        eligible_drivers: List of eligible drivers to prioritize
        ride: The ride request (used for distance calculations)
        fairness_weight: Weight factor for fairness vs efficiency (default: 1.0)

    Returns:
        List of drivers sorted by priority (best first)

    Algorithm:
        1. Primary sort: Lowest number of completed rides (fairness)
        2. Secondary sort: Shortest distance to pickup (efficiency)
        3. Optional: Apply fairness weight to balance priorities
    """
    if not eligible_drivers:
        return []

    # Calculate composite scores for each driver
    driver_scores = []
    for driver in eligible_drivers:
        # Fairness component: fewer completed rides is better
        fairness_score = driver.completed_rides

        # Efficiency component: shorter distance is better
        distance_to_pickup = manhattan_distance(
            driver.x, driver.y,
            ride.pickup_x, ride.pickup_y
        )

        # Composite score (lower is better)
        # Fairness is weighted, distance is normalized
        composite_score = (
            fairness_weight * fairness_score * 10 +  # Multiply by 10 to make fairness dominant
            distance_to_pickup
        )

        driver_scores.append((driver, composite_score, fairness_score, distance_to_pickup))

    # Sort by composite score (lower is better)
    # In case of tie in composite, use fairness, then distance
    driver_scores.sort(key=lambda x: (x[1], x[2], x[3]))

    # Return sorted list of drivers
    return [driver for driver, _, _, _ in driver_scores]


def dispatch_ride(ride_id: str, state: SimulationState) -> Tuple[bool, Optional[str]]:
    """
    Attempt to dispatch a ride to the best available driver

    Args:
        ride_id: ID of the ride request to dispatch
        state: Current simulation state

    Returns:
        Tuple of (success: bool, driver_id: Optional[str])
        Returns (True, driver_id) if dispatched successfully
        Returns (False, None) if no drivers available

    Side Effects:
        Updates ride and driver states if dispatch is successful
    """
    # Get the ride request
    ride = state.get_ride_request(ride_id)
    if not ride:
        logger.error(f"Ride {ride_id} not found")
        return False, None

    # Check if ride is in waiting status
    if ride.status != RideStatus.WAITING:
        logger.warning(f"Ride {ride_id} is not in WAITING status: {ride.status}")
        return False, None

    # Check if ride is in cooldown
    if ride.is_in_cooldown(state.current_tick):
        logger.info(f"Ride {ride_id} is in cooldown until tick {ride.cooldown_until_tick}")
        return False, None

    # Get available drivers
    available_drivers = state.get_available_drivers()
    if not available_drivers:
        logger.info(f"No available drivers for ride {ride_id}")
        return False, None

    # Find eligible drivers within search radius
    eligible_drivers = find_eligible_drivers(ride, available_drivers)
    if not eligible_drivers:
        logger.info(f"No eligible drivers within search radius for ride {ride_id}")
        return False, None

    # Prioritize drivers based on fairness and efficiency
    prioritized_drivers = prioritize_drivers(
        eligible_drivers, ride,
        fairness_weight=state.config.fairness_penalty
    )

    # Attempt to assign to the highest priority driver
    # Note: In the full implementation, we'll check driver acceptance
    # For now, we'll assume the first driver accepts
    if prioritized_drivers:
        best_driver = prioritized_drivers[0]

        # Assign the driver to the ride
        ride.assign_driver(best_driver.id)
        best_driver.status = DriverStatus.ASSIGNED
        best_driver.current_ride_id = ride.id
        best_driver.reset_idle_state()

        logger.info(f"Dispatched ride {ride_id} to driver {best_driver.id}")
        return True, best_driver.id

    return False, None


def attempt_fallback_dispatch(ride_id: str, rejected_driver_id: str,
                             state: SimulationState) -> Tuple[bool, Optional[str]]:
    """
    Attempt to dispatch a ride to the next best driver after rejection

    Args:
        ride_id: ID of the ride request to dispatch
        rejected_driver_id: ID of the driver who rejected the ride
        state: Current simulation state

    Returns:
        Tuple of (success: bool, driver_id: Optional[str])
        Returns (True, driver_id) if dispatched to another driver
        Returns (False, None) if no other drivers available
    """
    # Get the ride request
    ride = state.get_ride_request(ride_id)
    if not ride:
        logger.error(f"Ride {ride_id} not found")
        return False, None

    # Record the rejection
    ride.add_rejection(
        rejected_driver_id,
        state.current_tick,
        state.config.rejection_cooldown_ticks
    )

    # Reset ride status to waiting
    ride.status = RideStatus.WAITING
    ride.assigned_driver_id = None

    # After cooldown, try to dispatch again
    # For immediate fallback, temporarily clear cooldown
    original_cooldown = ride.cooldown_until_tick
    ride.cooldown_until_tick = None

    # Attempt dispatch with updated rejected list
    success, driver_id = dispatch_ride(ride_id, state)

    # Restore cooldown if dispatch failed
    if not success:
        ride.cooldown_until_tick = original_cooldown
        # Check if all available drivers have rejected
        available_drivers = state.get_available_drivers()
        all_rejected = all(
            driver.id in ride.rejected_driver_ids
            for driver in available_drivers
        )
        if all_rejected:
            ride.fail()
            logger.info(f"Ride {ride_id} failed - all drivers rejected")

    return success, driver_id


def batch_dispatch(state: SimulationState) -> Dict[str, str]:
    """
    Attempt to dispatch all waiting rides in the current tick

    Args:
        state: Current simulation state

    Returns:
        Dictionary mapping ride_id to assigned driver_id for successful dispatches
    """
    dispatched = {}

    # Get all waiting rides not in cooldown
    waiting_rides = state.get_waiting_rides()

    # Sort rides by creation time (FIFO)
    waiting_rides.sort(key=lambda r: r.created_tick)

    for ride in waiting_rides:
        success, driver_id = dispatch_ride(ride.id, state)
        if success and driver_id:
            dispatched[ride.id] = driver_id

    logger.info(f"Batch dispatch: {len(dispatched)} rides dispatched out of {len(waiting_rides)} waiting")
    return dispatched