"""
Simulation state management module for the ride dispatch system
Manages all entities in memory using Python dictionaries
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from .models import Driver, Rider, RideRequest, DriverStatus, RiderStatus, RideStatus


@dataclass
class SimulationConfig:
    """
    Configuration parameters for the simulation
    """
    initial_search_radius: int = 15  # Start with even larger radius
    max_search_radius: int = 100  # Full map coverage
    radius_growth_interval: int = 2  # Grow radius every 2 idle ticks (much faster)
    grid_size: int = 100
    rejection_cooldown_ticks: int = 5
    fairness_penalty: float = 1.0  # Weight for fairness in dispatch algorithm
    global_search_after_ticks: int = 10  # Make ride available everywhere after N ticks


class SimulationState:
    """
    Manages the complete state of the ride dispatch simulation
    Stores all entities in memory and provides access methods
    """

    def __init__(self):
        """
        Initialize an empty simulation state
        """
        self.drivers: Dict[str, Driver] = {}
        self.riders: Dict[str, Rider] = {}
        self.ride_requests: Dict[str, RideRequest] = {}
        self.current_tick: int = 0
        self.config: SimulationConfig = SimulationConfig()

    def reset(self) -> None:
        """
        Reset the simulation to initial empty state
        """
        self.drivers.clear()
        self.riders.clear()
        self.ride_requests.clear()
        self.current_tick = 0
        self.config = SimulationConfig()

    def add_driver(self, driver: Driver) -> None:
        """
        Add a driver to the simulation

        Args:
            driver: Driver instance to add

        Raises:
            ValueError: If driver with same ID already exists
        """
        if driver.id in self.drivers:
            raise ValueError(f"Driver with ID {driver.id} already exists")
        self.drivers[driver.id] = driver

    def add_rider(self, rider: Rider) -> None:
        """
        Add a rider to the simulation

        Args:
            rider: Rider instance to add

        Raises:
            ValueError: If rider with same ID already exists
        """
        if rider.id in self.riders:
            raise ValueError(f"Rider with ID {rider.id} already exists")
        self.riders[rider.id] = rider

    def add_ride_request(self, ride_request: RideRequest) -> None:
        """
        Add a ride request to the simulation

        Args:
            ride_request: RideRequest instance to add

        Raises:
            ValueError: If ride request with same ID already exists
        """
        if ride_request.id in self.ride_requests:
            raise ValueError(f"Ride request with ID {ride_request.id} already exists")
        ride_request.created_tick = self.current_tick
        self.ride_requests[ride_request.id] = ride_request

    def get_driver(self, driver_id: str) -> Optional[Driver]:
        """
        Get a driver by ID

        Args:
            driver_id: Driver ID to retrieve

        Returns:
            Driver instance or None if not found
        """
        return self.drivers.get(driver_id)

    def get_rider(self, rider_id: str) -> Optional[Rider]:
        """
        Get a rider by ID

        Args:
            rider_id: Rider ID to retrieve

        Returns:
            Rider instance or None if not found
        """
        return self.riders.get(rider_id)

    def get_ride_request(self, ride_id: str) -> Optional[RideRequest]:
        """
        Get a ride request by ID

        Args:
            ride_id: Ride request ID to retrieve

        Returns:
            RideRequest instance or None if not found
        """
        return self.ride_requests.get(ride_id)

    def get_available_drivers(self) -> List[Driver]:
        """
        Get all drivers with AVAILABLE status

        Returns:
            List of available drivers
        """
        return [
            driver for driver in self.drivers.values()
            if driver.status == DriverStatus.AVAILABLE
        ]

    def get_waiting_rides(self) -> List[RideRequest]:
        """
        Get all ride requests with WAITING status that are not in cooldown

        Returns:
            List of waiting ride requests not in cooldown
        """
        return [
            ride for ride in self.ride_requests.values()
            if ride.status == RideStatus.WAITING
            and not ride.is_in_cooldown(self.current_tick)
        ]

    def get_assigned_drivers(self) -> List[Driver]:
        """
        Get all drivers with ASSIGNED status

        Returns:
            List of assigned drivers
        """
        return [
            driver for driver in self.drivers.values()
            if driver.status == DriverStatus.ASSIGNED
        ]

    def get_on_trip_drivers(self) -> List[Driver]:
        """
        Get all drivers with ON_TRIP status

        Returns:
            List of drivers on trip
        """
        return [
            driver for driver in self.drivers.values()
            if driver.status == DriverStatus.ON_TRIP
        ]

    def increment_tick(self) -> None:
        """
        Increment the simulation tick counter
        """
        self.current_tick += 1

    def update_config(self, config_updates: Dict[str, Any]) -> None:
        """
        Update simulation configuration parameters

        Args:
            config_updates: Dictionary of configuration parameters to update
        """
        for key, value in config_updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                raise ValueError(f"Unknown configuration parameter: {key}")

    def get_state_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current simulation state

        Returns:
            Dictionary containing state summary statistics
        """
        return {
            "current_tick": self.current_tick,
            "total_drivers": len(self.drivers),
            "available_drivers": len(self.get_available_drivers()),
            "assigned_drivers": len(self.get_assigned_drivers()),
            "on_trip_drivers": len(self.get_on_trip_drivers()),
            "total_riders": len(self.riders),
            "total_ride_requests": len(self.ride_requests),
            "waiting_rides": len(self.get_waiting_rides()),
            "completed_rides": len([
                r for r in self.ride_requests.values()
                if r.status == RideStatus.COMPLETED
            ]),
            "failed_rides": len([
                r for r in self.ride_requests.values()
                if r.status == RideStatus.FAILED
            ])
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert entire state to dictionary for API responses

        Returns:
            Dictionary representation of complete state
        """
        return {
            "current_tick": self.current_tick,
            "config": {
                "initial_search_radius": self.config.initial_search_radius,
                "max_search_radius": self.config.max_search_radius,
                "radius_growth_interval": self.config.radius_growth_interval,
                "grid_size": self.config.grid_size,
                "rejection_cooldown_ticks": self.config.rejection_cooldown_ticks,
                "fairness_penalty": self.config.fairness_penalty
            },
            "drivers": {
                driver_id: driver.dict()
                for driver_id, driver in self.drivers.items()
            },
            "riders": {
                rider_id: rider.dict()
                for rider_id, rider in self.riders.items()
            },
            "ride_requests": {
                ride_id: ride.dict()
                for ride_id, ride in self.ride_requests.items()
            },
            "summary": self.get_state_summary()
        }


# Global state instance for API access
simulation_state = SimulationState()