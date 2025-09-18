"""
Status enumerations for the ride dispatch simulation system
"""
from enum import Enum


class DriverStatus(Enum):
    """
    Represents the possible states of a driver in the system
    """
    AVAILABLE = "available"  # Driver is available to accept rides
    ASSIGNED = "assigned"    # Driver is assigned to a ride, moving to pickup
    ON_TRIP = "on_trip"      # Driver has picked up rider, moving to dropoff
    OFFLINE = "offline"      # Driver is offline/inactive


class RiderStatus(Enum):
    """
    Represents the possible states of a rider in the system
    """
    WAITING = "waiting"      # Rider is waiting for a ride
    PICKED_UP = "picked_up"  # Rider has been picked up, on trip
    COMPLETED = "completed"  # Rider's trip has been completed


class RideStatus(Enum):
    """
    Represents the possible states of a ride request in the system
    """
    WAITING = "waiting"      # Ride request is waiting for driver assignment
    ASSIGNED = "assigned"    # Driver has been assigned, moving to pickup
    PICKUP = "pickup"        # Driver is at pickup location
    ON_TRIP = "on_trip"      # Rider picked up, moving to destination
    COMPLETED = "completed"  # Ride successfully completed
    FAILED = "failed"        # Ride failed (no drivers available, all rejected)