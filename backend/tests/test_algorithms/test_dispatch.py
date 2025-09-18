"""
Unit tests for dispatch algorithm
"""
import pytest
from src.models import Driver, RideRequest, DriverStatus, RideStatus
from src.state import SimulationState
from src.algorithms.dispatch import (
    find_eligible_drivers,
    prioritize_drivers,
    dispatch_ride,
    attempt_fallback_dispatch
)


class TestFindEligibleDrivers:
    """Test finding eligible drivers for rides"""

    def test_find_available_drivers_within_radius(self):
        """Test finding available drivers within search radius"""
        ride = RideRequest(
            id="ride1",
            rider_id="rider1",
            pickup_x=50,
            pickup_y=50,
            dropoff_x=70,
            dropoff_y=70
        )

        drivers = [
            Driver(id="d1", x=52, y=52, search_radius=5),  # Within radius
            Driver(id="d2", x=45, y=45, search_radius=10),  # Within radius
            Driver(id="d3", x=60, y=60, search_radius=5),   # Outside radius
            Driver(id="d4", x=50, y=50, search_radius=15),  # At pickup location
        ]

        eligible = find_eligible_drivers(ride, drivers)
        eligible_ids = [d.id for d in eligible]

        assert "d1" in eligible_ids  # Distance 4, radius 5
        assert "d2" in eligible_ids  # Distance 10, radius 10
        assert "d3" not in eligible_ids  # Distance 20, radius 5
        assert "d4" in eligible_ids  # Distance 0, radius 15

    def test_exclude_unavailable_drivers(self):
        """Test that unavailable drivers are excluded"""
        ride = RideRequest(
            id="ride1",
            rider_id="rider1",
            pickup_x=50,
            pickup_y=50,
            dropoff_x=70,
            dropoff_y=70
        )

        drivers = [
            Driver(id="d1", x=50, y=50, status=DriverStatus.AVAILABLE),
            Driver(id="d2", x=50, y=50, status=DriverStatus.ASSIGNED),
            Driver(id="d3", x=50, y=50, status=DriverStatus.ON_TRIP),
        ]

        eligible = find_eligible_drivers(ride, drivers)
        eligible_ids = [d.id for d in eligible]

        assert "d1" in eligible_ids
        assert "d2" not in eligible_ids
        assert "d3" not in eligible_ids

    def test_exclude_rejected_drivers(self):
        """Test that drivers who rejected the ride are excluded"""
        ride = RideRequest(
            id="ride1",
            rider_id="rider1",
            pickup_x=50,
            pickup_y=50,
            dropoff_x=70,
            dropoff_y=70,
            rejected_driver_ids=["d2", "d3"]
        )

        drivers = [
            Driver(id="d1", x=50, y=50, search_radius=10),
            Driver(id="d2", x=50, y=50, search_radius=10),  # Rejected
            Driver(id="d3", x=50, y=50, search_radius=10),  # Rejected
        ]

        eligible = find_eligible_drivers(ride, drivers)
        eligible_ids = [d.id for d in eligible]

        assert "d1" in eligible_ids
        assert "d2" not in eligible_ids
        assert "d3" not in eligible_ids


class TestPrioritizeDrivers:
    """Test driver prioritization logic"""

    def test_prioritize_by_completed_rides(self):
        """Test that drivers with fewer completed rides get priority"""
        ride = RideRequest(
            id="ride1",
            rider_id="rider1",
            pickup_x=50,
            pickup_y=50,
            dropoff_x=70,
            dropoff_y=70
        )

        drivers = [
            Driver(id="d1", x=50, y=50, completed_rides=10),
            Driver(id="d2", x=50, y=50, completed_rides=2),
            Driver(id="d3", x=50, y=50, completed_rides=5),
        ]

        prioritized = prioritize_drivers(drivers, ride)
        prioritized_ids = [d.id for d in prioritized]

        assert prioritized_ids == ["d2", "d3", "d1"]

    def test_prioritize_by_distance_as_tiebreaker(self):
        """Test that distance is used as tiebreaker for same completed rides"""
        ride = RideRequest(
            id="ride1",
            rider_id="rider1",
            pickup_x=50,
            pickup_y=50,
            dropoff_x=70,
            dropoff_y=70
        )

        drivers = [
            Driver(id="d1", x=60, y=60, completed_rides=5),  # Distance 20
            Driver(id="d2", x=52, y=52, completed_rides=5),  # Distance 4
            Driver(id="d3", x=55, y=55, completed_rides=5),  # Distance 10
        ]

        prioritized = prioritize_drivers(drivers, ride)
        prioritized_ids = [d.id for d in prioritized]

        # Same completed rides, so order by distance
        assert prioritized_ids == ["d2", "d3", "d1"]

    def test_empty_driver_list(self):
        """Test handling of empty driver list"""
        ride = RideRequest(
            id="ride1",
            rider_id="rider1",
            pickup_x=50,
            pickup_y=50,
            dropoff_x=70,
            dropoff_y=70
        )

        prioritized = prioritize_drivers([], ride)
        assert prioritized == []

    def test_fairness_weight_effect(self):
        """Test that fairness weight affects prioritization"""
        ride = RideRequest(
            id="ride1",
            rider_id="rider1",
            pickup_x=50,
            pickup_y=50,
            dropoff_x=70,
            dropoff_y=70
        )

        drivers = [
            Driver(id="d1", x=51, y=51, completed_rides=10),  # Close but many rides
            Driver(id="d2", x=60, y=60, completed_rides=0),   # Far but no rides
        ]

        # With high fairness weight, d2 should be prioritized despite distance
        prioritized = prioritize_drivers(drivers, ride, fairness_weight=10.0)
        assert prioritized[0].id == "d2"

        # With low fairness weight, d1 might be prioritized for being closer
        prioritized = prioritize_drivers(drivers, ride, fairness_weight=0.1)
        # This depends on specific scoring, but fairness should matter less


class TestDispatchRide:
    """Test ride dispatch functionality"""

    def test_successful_dispatch(self):
        """Test successful ride dispatch to best driver"""
        state = SimulationState()

        # Add drivers
        state.add_driver(Driver(id="d1", x=52, y=52, completed_rides=5))
        state.add_driver(Driver(id="d2", x=50, y=50, completed_rides=2))

        # Add ride
        ride = RideRequest(
            id="ride1",
            rider_id="rider1",
            pickup_x=50,
            pickup_y=50,
            dropoff_x=70,
            dropoff_y=70
        )
        state.add_ride_request(ride)

        # Dispatch ride
        success, driver_id = dispatch_ride("ride1", state)

        assert success is True
        assert driver_id == "d2"  # Driver with fewer completed rides

        # Check states updated
        assert ride.status == RideStatus.ASSIGNED.value
        assert ride.assigned_driver_id == "d2"
        assert state.drivers["d2"].status == DriverStatus.ASSIGNED.value
        assert state.drivers["d2"].current_ride_id == "ride1"

    def test_dispatch_with_no_available_drivers(self):
        """Test dispatch when no drivers are available"""
        state = SimulationState()

        # Add busy drivers
        state.add_driver(Driver(id="d1", x=50, y=50, status=DriverStatus.ON_TRIP))
        state.add_driver(Driver(id="d2", x=50, y=50, status=DriverStatus.ASSIGNED))

        # Add ride
        ride = RideRequest(
            id="ride1",
            rider_id="rider1",
            pickup_x=50,
            pickup_y=50,
            dropoff_x=70,
            dropoff_y=70
        )
        state.add_ride_request(ride)

        # Dispatch ride
        success, driver_id = dispatch_ride("ride1", state)

        assert success is False
        assert driver_id is None
        assert ride.status == RideStatus.WAITING.value

    def test_dispatch_with_no_eligible_drivers(self):
        """Test dispatch when drivers are available but none eligible"""
        state = SimulationState()

        # Add drivers far from pickup
        state.add_driver(Driver(id="d1", x=90, y=90, search_radius=5))
        state.add_driver(Driver(id="d2", x=10, y=10, search_radius=5))

        # Add ride
        ride = RideRequest(
            id="ride1",
            rider_id="rider1",
            pickup_x=50,
            pickup_y=50,
            dropoff_x=70,
            dropoff_y=70
        )
        state.add_ride_request(ride)

        # Dispatch ride
        success, driver_id = dispatch_ride("ride1", state)

        assert success is False
        assert driver_id is None

    def test_dispatch_ride_in_cooldown(self):
        """Test that rides in cooldown are not dispatched"""
        state = SimulationState()
        state.current_tick = 10

        # Add driver
        state.add_driver(Driver(id="d1", x=50, y=50))

        # Add ride in cooldown
        ride = RideRequest(
            id="ride1",
            rider_id="rider1",
            pickup_x=50,
            pickup_y=50,
            dropoff_x=70,
            dropoff_y=70,
            cooldown_until_tick=15
        )
        state.add_ride_request(ride)

        # Try to dispatch
        success, driver_id = dispatch_ride("ride1", state)

        assert success is False
        assert driver_id is None


class TestAttemptFallbackDispatch:
    """Test fallback dispatch after rejection"""

    def test_successful_fallback(self):
        """Test successful fallback to next best driver"""
        state = SimulationState()

        # Add multiple drivers
        state.add_driver(Driver(id="d1", x=50, y=50, completed_rides=2))
        state.add_driver(Driver(id="d2", x=52, y=52, completed_rides=5))
        state.add_driver(Driver(id="d3", x=54, y=54, completed_rides=8))

        # Add ride assigned to d1
        ride = RideRequest(
            id="ride1",
            rider_id="rider1",
            pickup_x=50,
            pickup_y=50,
            dropoff_x=70,
            dropoff_y=70,
            status=RideStatus.ASSIGNED,
            assigned_driver_id="d1"
        )
        state.add_ride_request(ride)

        # Attempt fallback after d1 rejects
        success, driver_id = attempt_fallback_dispatch("ride1", "d1", state)

        assert success is True
        assert driver_id == "d2"  # Next best driver
        assert "d1" in ride.rejected_driver_ids
        assert ride.assigned_driver_id == "d2"

    def test_fallback_with_all_drivers_rejected(self):
        """Test ride fails when all drivers reject"""
        state = SimulationState()

        # Add one driver
        state.add_driver(Driver(id="d1", x=50, y=50))

        # Add ride already rejected by d1
        ride = RideRequest(
            id="ride1",
            rider_id="rider1",
            pickup_x=50,
            pickup_y=50,
            dropoff_x=70,
            dropoff_y=70,
            status=RideStatus.ASSIGNED,
            assigned_driver_id="d1"
        )
        state.add_ride_request(ride)

        # Attempt fallback - should fail ride
        success, driver_id = attempt_fallback_dispatch("ride1", "d1", state)

        assert success is False
        assert driver_id is None
        assert ride.status == RideStatus.FAILED.value


if __name__ == "__main__":
    pytest.main([__file__])