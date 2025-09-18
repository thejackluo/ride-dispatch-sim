"""
Driver model for the ride dispatch simulation system
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from .enums import DriverStatus


class Driver(BaseModel):
    """
    Represents a driver in the ride dispatch system
    """
    id: str = Field(..., description="Unique driver identifier")
    x: int = Field(..., ge=0, le=99, description="Current x-coordinate on grid (0-99)")
    y: int = Field(..., ge=0, le=99, description="Current y-coordinate on grid (0-99)")
    status: DriverStatus = Field(
        default=DriverStatus.AVAILABLE,
        description="Current driver status"
    )
    search_radius: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Current search radius for accepting rides (1-20 units)"
    )
    completed_rides: int = Field(
        default=0,
        ge=0,
        description="Total number of successfully completed rides"
    )
    idle_ticks: int = Field(
        default=0,
        ge=0,
        description="Number of ticks spent idle (for radius growth calculation)"
    )
    current_ride_id: Optional[str] = Field(
        default=None,
        description="ID of the currently assigned/active ride"
    )

    @field_validator('x', 'y')
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

    @field_validator('search_radius')
    @classmethod
    def validate_search_radius(cls, v: int) -> int:
        """
        Validates that search radius is within allowed range (1-20)

        Args:
            v: The search radius value to validate

        Returns:
            int: The validated search radius value

        Raises:
            ValueError: If radius is outside valid range
        """
        if not 1 <= v <= 20:
            raise ValueError(f"Search radius must be between 1 and 20, got {v}")
        return v

    def is_available(self) -> bool:
        """
        Check if driver is available to accept new rides

        Returns:
            bool: True if driver status is AVAILABLE, False otherwise
        """
        return self.status == DriverStatus.AVAILABLE

    def reset_idle_state(self) -> None:
        """
        Reset idle-related state when driver becomes active
        Typically called when driver accepts a ride
        """
        self.idle_ticks = 0
        self.search_radius = 5  # Reset to initial radius

    def increment_idle_tick(self) -> None:
        """
        Increment idle tick counter and potentially grow search radius
        Called each tick when driver is available but not assigned
        """
        if self.status == DriverStatus.AVAILABLE:
            self.idle_ticks += 1
            # Grow search radius every 10 idle ticks, up to max of 20
            if self.idle_ticks > 0 and self.idle_ticks % 10 == 0:
                self.search_radius = min(20, self.search_radius + 1)

    model_config = ConfigDict(use_enum_values=True)