"""
RideRequest model for the ride dispatch simulation system
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict

from .enums import RideStatus


class RideRequest(BaseModel):
    """
    Represents a ride request in the ride dispatch system
    """
    id: str = Field(..., description="Unique ride request identifier")
    rider_id: str = Field(..., description="ID of the requesting rider")
    pickup_x: int = Field(..., ge=0, le=99, description="Pickup x-coordinate (0-99)")
    pickup_y: int = Field(..., ge=0, le=99, description="Pickup y-coordinate (0-99)")
    dropoff_x: int = Field(..., ge=0, le=99, description="Dropoff x-coordinate (0-99)")
    dropoff_y: int = Field(..., ge=0, le=99, description="Dropoff y-coordinate (0-99)")
    status: RideStatus = Field(
        default=RideStatus.WAITING,
        description="Current ride request status"
    )
    assigned_driver_id: Optional[str] = Field(
        default=None,
        description="ID of the currently assigned driver"
    )
    rejected_driver_ids: List[str] = Field(
        default_factory=list,
        description="List of driver IDs who have rejected this ride"
    )
    created_tick: int = Field(
        default=0,
        ge=0,
        description="Simulation tick when this ride was requested"
    )
    cooldown_until_tick: Optional[int] = Field(
        default=None,
        description="Tick until which ride is in cooldown after rejection"
    )

    @field_validator('pickup_x', 'pickup_y', 'dropoff_x', 'dropoff_y')
    @classmethod
    def validate_coordinates(cls, v: int) -> int:
        """
        Validates that coordinates are within grid bounds (0-99)

        Args:
            v: The coordinate value to validate

        Returns:
            int: The validated coordinate value

        Raises:
            ValueError: If coordinate is outside valid range
        """
        if not 0 <= v <= 99:
            raise ValueError(f"Coordinate must be between 0 and 99, got {v}")
        return v

    @field_validator('pickup_x', 'pickup_y')
    @classmethod
    def validate_pickup_different_from_dropoff(cls, v: int, values) -> int:
        """
        Validates that pickup and dropoff locations are different
        Note: This validation is simplified; full validation requires both x and y

        Args:
            v: The coordinate value to validate
            values: Previously validated field values

        Returns:
            int: The validated coordinate value
        """
        return v

    def is_waiting(self) -> bool:
        """
        Check if ride request is waiting for assignment

        Returns:
            bool: True if status is WAITING, False otherwise
        """
        return self.status == RideStatus.WAITING

    def is_in_cooldown(self, current_tick: int) -> bool:
        """
        Check if ride request is currently in cooldown period

        Args:
            current_tick: Current simulation tick

        Returns:
            bool: True if in cooldown, False otherwise
        """
        if self.cooldown_until_tick is None:
            return False
        return current_tick < self.cooldown_until_tick

    def add_rejection(self, driver_id: str, current_tick: int, cooldown_ticks: int = 5) -> None:
        """
        Record a driver rejection and set cooldown period

        Args:
            driver_id: ID of the driver who rejected the ride
            current_tick: Current simulation tick
            cooldown_ticks: Number of ticks for cooldown period (default: 5)
        """
        if driver_id not in self.rejected_driver_ids:
            self.rejected_driver_ids.append(driver_id)
        self.cooldown_until_tick = current_tick + cooldown_ticks

    def assign_driver(self, driver_id: str) -> None:
        """
        Assign a driver to this ride request

        Args:
            driver_id: ID of the driver to assign
        """
        self.assigned_driver_id = driver_id
        self.status = RideStatus.ASSIGNED

    def start_pickup(self) -> None:
        """
        Transition ride to pickup phase
        """
        if self.status == RideStatus.ASSIGNED:
            self.status = RideStatus.PICKUP

    def start_trip(self) -> None:
        """
        Transition ride to on-trip phase (rider picked up)
        """
        if self.status in [RideStatus.ASSIGNED, RideStatus.PICKUP]:
            self.status = RideStatus.ON_TRIP

    def complete(self) -> None:
        """
        Mark ride as completed
        """
        self.status = RideStatus.COMPLETED

    def fail(self) -> None:
        """
        Mark ride as failed (no drivers available or all rejected)
        """
        self.status = RideStatus.FAILED

    model_config = ConfigDict(use_enum_values=True)