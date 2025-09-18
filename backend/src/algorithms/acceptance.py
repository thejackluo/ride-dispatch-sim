"""
Driver acceptance logic for the ride dispatch simulation system
Determines whether a driver accepts or rejects a ride request
"""
import logging
from typing import Optional

from ..models import Driver, RideRequest, DriverStatus, RideStatus
from ..utils.geometry import manhattan_distance, is_within_radius
from ..state import SimulationState

logger = logging.getLogger(__name__)


def should_accept_ride(driver: Driver, ride: RideRequest) -> bool:
    """
    Determine if a driver should accept a ride request
    Based on pickup location being within driver's search radius

    Args:
        driver: The driver being offered the ride
        ride: The ride request being offered

    Returns:
        bool: True if driver should accept, False if should reject

    Decision Criteria:
        - Pickup location must be within driver's current search radius
        - Uses Manhattan distance for radius calculation
    """
    # Check if driver is available
    if driver.status != DriverStatus.AVAILABLE:
        logger.warning(f"Driver {driver.id} is not available (status: {driver.status})")
        return False

    # Check if pickup is within driver's search radius
    within_radius = is_within_radius(
        driver.x, driver.y,
        ride.pickup_x, ride.pickup_y,
        driver.search_radius
    )

    if not within_radius:
        distance = manhattan_distance(
            driver.x, driver.y,
            ride.pickup_x, ride.pickup_y
        )
        logger.info(
            f"Driver {driver.id} rejecting ride {ride.id}: "
            f"pickup distance {distance} exceeds search radius {driver.search_radius}"
        )

    return within_radius


def process_driver_response(driver_id: str, ride_id: str,
                          accepted: bool, state: SimulationState) -> bool:
    """
    Process a driver's response to a ride offer

    Args:
        driver_id: ID of the driver responding
        ride_id: ID of the ride being responded to
        accepted: Whether the driver accepted the ride
        state: Current simulation state

    Returns:
        bool: True if response was processed successfully, False otherwise

    Side Effects:
        - Updates ride and driver states based on acceptance/rejection
        - Triggers fallback dispatch if ride is rejected
    """
    # Get driver and ride from state
    driver = state.get_driver(driver_id)
    ride = state.get_ride_request(ride_id)

    if not driver:
        logger.error(f"Driver {driver_id} not found")
        return False

    if not ride:
        logger.error(f"Ride {ride_id} not found")
        return False

    # Validate that this driver is assigned to this ride
    if ride.assigned_driver_id != driver_id:
        logger.warning(
            f"Driver {driver_id} is not assigned to ride {ride_id} "
            f"(assigned: {ride.assigned_driver_id})"
        )
        return False

    if accepted:
        # Driver accepts the ride
        logger.info(f"Driver {driver_id} accepted ride {ride_id}")

        # Update driver state
        driver.status = DriverStatus.ASSIGNED
        driver.current_ride_id = ride_id
        driver.reset_idle_state()

        # Ride remains in ASSIGNED status
        # (will transition to PICKUP when driver reaches pickup location)
        return True

    else:
        # Driver rejects the ride
        logger.info(f"Driver {driver_id} rejected ride {ride_id}")

        # Update driver state back to available
        driver.status = DriverStatus.AVAILABLE
        driver.current_ride_id = None

        # Record rejection and add cooldown
        ride.add_rejection(
            driver_id,
            state.current_tick,
            state.config.rejection_cooldown_ticks
        )

        # Reset ride to waiting status
        ride.status = RideStatus.WAITING
        ride.assigned_driver_id = None

        # Attempt fallback dispatch to next best driver
        from .dispatch import attempt_fallback_dispatch
        success, new_driver_id = attempt_fallback_dispatch(ride_id, driver_id, state)

        if success:
            logger.info(f"Ride {ride_id} reassigned to driver {new_driver_id} after rejection")
        else:
            logger.warning(f"Failed to find fallback driver for ride {ride_id}")

        return True


def auto_process_acceptance(driver_id: str, ride_id: str,
                           state: SimulationState) -> bool:
    """
    Automatically process driver acceptance decision based on algorithm

    Args:
        driver_id: ID of the driver to process
        ride_id: ID of the ride to process
        state: Current simulation state

    Returns:
        bool: True if driver accepted, False if rejected

    Note:
        This function combines should_accept_ride with process_driver_response
        for automatic simulation processing
    """
    driver = state.get_driver(driver_id)
    ride = state.get_ride_request(ride_id)

    if not driver or not ride:
        logger.error(f"Driver {driver_id} or ride {ride_id} not found")
        return False

    # Determine if driver should accept
    accepted = should_accept_ride(driver, ride)

    # Process the response
    process_driver_response(driver_id, ride_id, accepted, state)

    return accepted


def check_driver_workload(driver: Driver, max_rides_per_shift: int = 20) -> bool:
    """
    Check if driver has capacity for more rides based on workload

    Args:
        driver: The driver to check
        max_rides_per_shift: Maximum rides allowed per shift (default: 20)

    Returns:
        bool: True if driver can take more rides, False if at capacity

    Note:
        This is an optional enhancement for workload-based acceptance
        Not required by base requirements but useful for realistic simulation
    """
    return driver.completed_rides < max_rides_per_shift


def calculate_acceptance_probability(driver: Driver, ride: RideRequest,
                                    base_probability: float = 0.9) -> float:
    """
    Calculate probability of driver accepting a ride (for stochastic simulation)

    Args:
        driver: The driver being offered the ride
        ride: The ride request being offered
        base_probability: Base acceptance probability (default: 0.9)

    Returns:
        float: Probability of acceptance (0.0 to 1.0)

    Factors:
        - Distance to pickup (closer = higher probability)
        - Driver's completed rides (fewer = higher probability)
        - Time ride has been waiting (longer = higher probability)

    Note:
        This is an optional enhancement for probabilistic acceptance
        Not used in deterministic simulation mode
    """
    # Start with base probability
    probability = base_probability

    # Factor 1: Distance to pickup (normalized)
    distance = manhattan_distance(
        driver.x, driver.y,
        ride.pickup_x, ride.pickup_y
    )
    max_distance = driver.search_radius
    if max_distance > 0:
        distance_factor = 1.0 - (distance / max_distance)
        probability *= (0.7 + 0.3 * distance_factor)

    # Factor 2: Driver fatigue (more rides = lower probability)
    if driver.completed_rides > 10:
        fatigue_factor = max(0.5, 1.0 - (driver.completed_rides - 10) * 0.05)
        probability *= fatigue_factor

    # Factor 3: Ride wait time (longer wait = higher probability)
    # This would require access to current_tick, so simplified here
    # In practice, would use: wait_time = current_tick - ride.created_tick

    return min(1.0, max(0.0, probability))