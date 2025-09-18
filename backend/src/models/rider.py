"""
Rider model for the ride dispatch simulation system
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator

from .enums import RiderStatus


class Rider(BaseModel):
    """
    Represents a rider in the ride dispatch system
    """
    id: str = Field(..., description="Unique rider identifier")
    x: int = Field(..., ge=0, le=99, description="Current x-coordinate on grid (0-99)")
    y: int = Field(..., ge=0, le=99, description="Current y-coordinate on grid (0-99)")
    status: RiderStatus = Field(
        default=RiderStatus.WAITING,
        description="Current rider status"
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

    def is_waiting(self) -> bool:
        """
        Check if rider is waiting for a ride

        Returns:
            bool: True if rider status is WAITING, False otherwise
        """
        return self.status == RiderStatus.WAITING

    def update_location(self, x: int, y: int) -> None:
        """
        Update rider's location on the grid

        Args:
            x: New x-coordinate (0-99)
            y: New y-coordinate (0-99)

        Raises:
            ValueError: If coordinates are outside valid range
        """
        if not 0 <= x <= 99 or not 0 <= y <= 99:
            raise ValueError(f"Invalid coordinates: ({x}, {y}). Must be within 0-99")
        self.x = x
        self.y = y

    model_config = ConfigDict(use_enum_values=True)