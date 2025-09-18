"""
Driver movement and behavior algorithms for the ride dispatch simulation system
Handles random movement and search radius updates
"""
import random
import logging
from typing import Tuple, Optional, List
from enum import Enum

from ..models import Driver, RideRequest, DriverStatus, RideStatus, RiderStatus
from ..utils.geometry import manhattan_distance, clamp_to_grid
from ..state import SimulationState, SimulationConfig

logger = logging.getLogger(__name__)


class Direction(Enum):
    """Movement directions on the grid"""
    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


def move_driver_randomly(driver: Driver, grid_size: int = 100) -> Tuple[int, int]:
    """
    Move an available driver randomly one grid unit per tick

    Args:
        driver: The driver to move
        grid_size: Size of the grid (default: 100)

    Returns:
        Tuple[int, int]: New (x, y) coordinates after movement

    Movement Rules:
        - Only moves if driver status is AVAILABLE
        - Moves exactly one grid unit per tick
        - Valid moves: up, down, left, right (no diagonal)
        - Stays within grid boundaries (0 to grid_size-1)
    """
    # Only move available drivers
    if driver.status != DriverStatus.AVAILABLE:
        return driver.x, driver.y

    # Choose random direction
    direction = random.choice(list(Direction))
    dx, dy = direction.value

    # Calculate new position
    new_x = driver.x + dx
    new_y = driver.y + dy

    # Clamp to grid boundaries
    new_x, new_y = clamp_to_grid(new_x, new_y, grid_size)

    # Update driver position
    driver.x = new_x
    driver.y = new_y

    logger.debug(f"Driver {driver.id} moved to ({new_x}, {new_y})")
    return new_x, new_y


def move_driver_toward_target(driver: Driver, target_x: int, target_y: int,
                             grid_size: int = 100) -> Tuple[int, int]:
    """
    Move a driver one step toward a target location

    Args:
        driver: The driver to move
        target_x: Target x-coordinate
        target_y: Target y-coordinate
        grid_size: Size of the grid (default: 100)

    Returns:
        Tuple[int, int]: New (x, y) coordinates after movement

    Movement Strategy:
        - Moves one grid unit per tick toward target
        - Prioritizes the axis with greater distance
        - Handles grid boundaries
    """
    # If already at target, don't move
    if driver.x == target_x and driver.y == target_y:
        return driver.x, driver.y

    # Calculate distances on each axis
    dx = target_x - driver.x
    dy = target_y - driver.y

    # Determine movement direction
    new_x, new_y = driver.x, driver.y

    # Move on the axis with greater distance
    # If equal, randomly choose
    if abs(dx) > abs(dy):
        # Move horizontally
        new_x += 1 if dx > 0 else -1
    elif abs(dy) > abs(dx):
        # Move vertically
        new_y += 1 if dy > 0 else -1
    else:
        # Equal distance, choose randomly
        if random.random() < 0.5:
            new_x += 1 if dx > 0 else -1
        else:
            new_y += 1 if dy > 0 else -1

    # Clamp to grid boundaries
    new_x, new_y = clamp_to_grid(new_x, new_y, grid_size)

    # Update driver position
    driver.x = new_x
    driver.y = new_y

    return new_x, new_y


def update_driver_search_radius(driver: Driver, config: SimulationConfig) -> int:
    """
    Update a driver's search radius based on idle time

    Args:
        driver: The driver to update
        config: Simulation configuration

    Returns:
        int: Updated search radius

    Growth Rules:
        - Only grows for AVAILABLE drivers
        - Increases by 1 unit every radius_growth_interval ticks
        - Capped at max_search_radius
        - Resets to initial_search_radius when driver accepts a ride
    """
    # Only update for available drivers
    if driver.status != DriverStatus.AVAILABLE:
        return driver.search_radius

    # Increment idle tick counter
    driver.idle_ticks += 1

    # Check if radius should grow
    if (driver.idle_ticks > 0 and
        driver.idle_ticks % config.radius_growth_interval == 0):

        # Increase radius up to maximum
        old_radius = driver.search_radius
        driver.search_radius = min(
            config.max_search_radius,
            driver.search_radius + 1
        )

        if driver.search_radius > old_radius:
            logger.info(
                f"Driver {driver.id} search radius increased from "
                f"{old_radius} to {driver.search_radius} after "
                f"{driver.idle_ticks} idle ticks"
            )

    return driver.search_radius


def process_driver_movement(driver: Driver, state: SimulationState) -> None:
    """
    Process movement for a driver based on their current status

    Args:
        driver: The driver to move
        state: Current simulation state

    Movement Logic:
        - AVAILABLE: Move randomly
        - ASSIGNED: Move toward pickup location
        - ON_TRIP: Move toward dropoff location
    """
    if driver.status == DriverStatus.AVAILABLE:
        # Random movement for available drivers
        move_driver_randomly(driver, state.config.grid_size)

        # Update search radius based on idle time
        update_driver_search_radius(driver, state.config)

    elif driver.status == DriverStatus.ASSIGNED:
        # Move toward pickup location
        if driver.current_ride_id:
            ride = state.get_ride_request(driver.current_ride_id)
            if ride:
                move_driver_toward_target(
                    driver, ride.pickup_x, ride.pickup_y,
                    state.config.grid_size
                )

                # Check if reached pickup location
                if driver.x == ride.pickup_x and driver.y == ride.pickup_y:
                    # Transition to pickup phase
                    driver.status = DriverStatus.ON_TRIP
                    ride.start_trip()

                    # Update rider location to driver location
                    rider = state.get_rider(ride.rider_id)
                    if rider:
                        rider.x = driver.x
                        rider.y = driver.y
                        rider.status = RiderStatus.PICKED_UP

                    logger.info(f"Driver {driver.id} picked up rider for ride {ride.id}")

    elif driver.status == DriverStatus.ON_TRIP:
        # Move toward dropoff location
        if driver.current_ride_id:
            ride = state.get_ride_request(driver.current_ride_id)
            if ride:
                move_driver_toward_target(
                    driver, ride.dropoff_x, ride.dropoff_y,
                    state.config.grid_size
                )

                # Update rider location to match driver
                rider = state.get_rider(ride.rider_id)
                if rider:
                    rider.x = driver.x
                    rider.y = driver.y

                # Check if reached dropoff location
                if driver.x == ride.dropoff_x and driver.y == ride.dropoff_y:
                    # Complete the ride
                    complete_ride(driver, ride, state)


def complete_ride(driver: Driver, ride: RideRequest,
                 state: SimulationState) -> None:
    """
    Complete a ride and update all related states

    Args:
        driver: The driver completing the ride
        ride: The ride being completed
        state: Current simulation state
    """
    # Update ride status
    ride.complete()

    # Update driver
    driver.status = DriverStatus.AVAILABLE
    driver.current_ride_id = None
    driver.completed_rides += 1
    driver.idle_ticks = 0  # Reset idle counter

    # Update rider
    rider = state.get_rider(ride.rider_id)
    if rider:
        rider.status = RiderStatus.COMPLETED

    logger.info(
        f"Ride {ride.id} completed by driver {driver.id}. "
        f"Driver has completed {driver.completed_rides} total rides"
    )


def process_all_driver_movements(state: SimulationState) -> None:
    """
    Process movement for all drivers in the simulation

    Args:
        state: Current simulation state
    """
    for driver in state.drivers.values():
        process_driver_movement(driver, state)


def get_nearby_drivers(x: int, y: int, radius: int,
                      state: SimulationState) -> List[Driver]:
    """
    Find all drivers within a given radius of a location

    Args:
        x: X-coordinate of center point
        y: Y-coordinate of center point
        radius: Search radius
        state: Current simulation state

    Returns:
        List of drivers within the specified radius
    """
    nearby_drivers = []

    for driver in state.drivers.values():
        distance = manhattan_distance(x, y, driver.x, driver.y)
        if distance <= radius:
            nearby_drivers.append(driver)

    return nearby_drivers