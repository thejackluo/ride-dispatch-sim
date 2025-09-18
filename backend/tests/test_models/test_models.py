"""
Unit tests for data models
"""
import pytest
from pydantic import ValidationError
from src.models import (
    Driver, Rider, RideRequest,
    DriverStatus, RiderStatus, RideStatus
)


class TestDriverModel:
    """Test Driver model"""

    def test_create_driver_with_defaults(self):
        """Test creating driver with default values"""
        driver = Driver(id="driver1", x=50, y=50)
        assert driver.id == "driver1"
        assert driver.x == 50
        assert driver.y == 50
        assert driver.status == DriverStatus.AVAILABLE.value
        assert driver.search_radius == 5
        assert driver.completed_rides == 0
        assert driver.idle_ticks == 0
        assert driver.current_ride_id is None

    def test_create_driver_with_custom_values(self):
        """Test creating driver with custom values"""
        driver = Driver(
            id="driver2",
            x=25,
            y=75,
            status=DriverStatus.ON_TRIP,
            search_radius=10,
            completed_rides=5,
            idle_ticks=30,
            current_ride_id="ride123"
        )
        assert driver.x == 25
        assert driver.y == 75
        assert driver.status == DriverStatus.ON_TRIP.value
        assert driver.search_radius == 10
        assert driver.completed_rides == 5
        assert driver.idle_ticks == 30
        assert driver.current_ride_id == "ride123"

    def test_invalid_coordinates(self):
        """Test validation of invalid coordinates"""
        with pytest.raises(ValidationError):
            Driver(id="driver3", x=-1, y=50)
        with pytest.raises(ValidationError):
            Driver(id="driver3", x=50, y=100)

    def test_invalid_search_radius(self):
        """Test validation of invalid search radius"""
        with pytest.raises(ValidationError):
            Driver(id="driver3", x=50, y=50, search_radius=0)
        with pytest.raises(ValidationError):
            Driver(id="driver3", x=50, y=50, search_radius=21)

    def test_is_available_method(self):
        """Test is_available method"""
        driver = Driver(id="driver4", x=50, y=50)
        assert driver.is_available() is True

        driver.status = DriverStatus.ON_TRIP.value
        assert driver.is_available() is False

    def test_reset_idle_state(self):
        """Test reset_idle_state method"""
        driver = Driver(id="driver5", x=50, y=50, idle_ticks=50, search_radius=15)
        driver.reset_idle_state()
        assert driver.idle_ticks == 0
        assert driver.search_radius == 5

    def test_increment_idle_tick(self):
        """Test increment_idle_tick method"""
        driver = Driver(id="driver6", x=50, y=50)

        # Test increment for available driver
        for i in range(1, 10):
            driver.increment_idle_tick()
            assert driver.idle_ticks == i
            assert driver.search_radius == 5  # No growth yet

        # Test radius growth at 10 ticks
        driver.increment_idle_tick()
        assert driver.idle_ticks == 10
        assert driver.search_radius == 6  # Should have grown

        # Test no increment when not available
        driver.status = DriverStatus.ON_TRIP.value
        driver.increment_idle_tick()
        assert driver.idle_ticks == 10  # Should not change


class TestRiderModel:
    """Test Rider model"""

    def test_create_rider_with_defaults(self):
        """Test creating rider with default values"""
        rider = Rider(id="rider1", x=30, y=40)
        assert rider.id == "rider1"
        assert rider.x == 30
        assert rider.y == 40
        assert rider.status == RiderStatus.WAITING.value

    def test_create_rider_with_custom_status(self):
        """Test creating rider with custom status"""
        rider = Rider(
            id="rider2",
            x=60,
            y=70,
            status=RiderStatus.PICKED_UP
        )
        assert rider.status == RiderStatus.PICKED_UP.value

    def test_invalid_rider_coordinates(self):
        """Test validation of invalid rider coordinates"""
        with pytest.raises(ValidationError):
            Rider(id="rider3", x=-10, y=50)
        with pytest.raises(ValidationError):
            Rider(id="rider3", x=50, y=150)

    def test_is_waiting_method(self):
        """Test is_waiting method"""
        rider = Rider(id="rider4", x=50, y=50)
        assert rider.is_waiting() is True

        rider.status = RiderStatus.PICKED_UP.value
        assert rider.is_waiting() is False

    def test_update_location(self):
        """Test update_location method"""
        rider = Rider(id="rider5", x=50, y=50)
        rider.update_location(75, 25)
        assert rider.x == 75
        assert rider.y == 25

        # Test invalid location update
        with pytest.raises(ValueError):
            rider.update_location(100, 50)


class TestRideRequestModel:
    """Test RideRequest model"""

    def test_create_ride_request_with_defaults(self):
        """Test creating ride request with default values"""
        ride = RideRequest(
            id="ride1",
            rider_id="rider1",
            pickup_x=10,
            pickup_y=20,
            dropoff_x=80,
            dropoff_y=90
        )
        assert ride.id == "ride1"
        assert ride.rider_id == "rider1"
        assert ride.pickup_x == 10
        assert ride.pickup_y == 20
        assert ride.dropoff_x == 80
        assert ride.dropoff_y == 90
        assert ride.status == RideStatus.WAITING.value
        assert ride.assigned_driver_id is None
        assert ride.rejected_driver_ids == []
        assert ride.created_tick == 0
        assert ride.cooldown_until_tick is None

    def test_create_ride_request_with_custom_values(self):
        """Test creating ride request with custom values"""
        ride = RideRequest(
            id="ride2",
            rider_id="rider2",
            pickup_x=30,
            pickup_y=40,
            dropoff_x=60,
            dropoff_y=70,
            status=RideStatus.ASSIGNED,
            assigned_driver_id="driver1",
            rejected_driver_ids=["driver2", "driver3"],
            created_tick=15,
            cooldown_until_tick=20
        )
        assert ride.status == RideStatus.ASSIGNED.value
        assert ride.assigned_driver_id == "driver1"
        assert ride.rejected_driver_ids == ["driver2", "driver3"]
        assert ride.created_tick == 15
        assert ride.cooldown_until_tick == 20

    def test_invalid_ride_coordinates(self):
        """Test validation of invalid ride coordinates"""
        with pytest.raises(ValidationError):
            RideRequest(
                id="ride3",
                rider_id="rider3",
                pickup_x=-5,
                pickup_y=50,
                dropoff_x=80,
                dropoff_y=90
            )
        with pytest.raises(ValidationError):
            RideRequest(
                id="ride3",
                rider_id="rider3",
                pickup_x=50,
                pickup_y=50,
                dropoff_x=100,
                dropoff_y=90
            )

    def test_is_waiting_method(self):
        """Test is_waiting method"""
        ride = RideRequest(
            id="ride4",
            rider_id="rider4",
            pickup_x=10,
            pickup_y=20,
            dropoff_x=80,
            dropoff_y=90
        )
        assert ride.is_waiting() is True

        ride.status = RideStatus.ASSIGNED.value
        assert ride.is_waiting() is False

    def test_is_in_cooldown(self):
        """Test is_in_cooldown method"""
        ride = RideRequest(
            id="ride5",
            rider_id="rider5",
            pickup_x=10,
            pickup_y=20,
            dropoff_x=80,
            dropoff_y=90
        )

        # No cooldown initially
        assert ride.is_in_cooldown(10) is False

        # Set cooldown
        ride.cooldown_until_tick = 20
        assert ride.is_in_cooldown(15) is True
        assert ride.is_in_cooldown(20) is False
        assert ride.is_in_cooldown(25) is False

    def test_add_rejection(self):
        """Test add_rejection method"""
        ride = RideRequest(
            id="ride6",
            rider_id="rider6",
            pickup_x=10,
            pickup_y=20,
            dropoff_x=80,
            dropoff_y=90
        )

        ride.add_rejection("driver1", current_tick=10, cooldown_ticks=5)
        assert "driver1" in ride.rejected_driver_ids
        assert ride.cooldown_until_tick == 15

        # Test duplicate rejection
        ride.add_rejection("driver1", current_tick=12, cooldown_ticks=5)
        assert ride.rejected_driver_ids.count("driver1") == 1
        assert ride.cooldown_until_tick == 17

    def test_assign_driver(self):
        """Test assign_driver method"""
        ride = RideRequest(
            id="ride7",
            rider_id="rider7",
            pickup_x=10,
            pickup_y=20,
            dropoff_x=80,
            dropoff_y=90
        )

        ride.assign_driver("driver1")
        assert ride.assigned_driver_id == "driver1"
        assert ride.status == RideStatus.ASSIGNED.value

    def test_status_transitions(self):
        """Test ride status transition methods"""
        ride = RideRequest(
            id="ride8",
            rider_id="rider8",
            pickup_x=10,
            pickup_y=20,
            dropoff_x=80,
            dropoff_y=90
        )

        # Start as waiting
        assert ride.status == RideStatus.WAITING.value

        # Assign driver
        ride.assign_driver("driver1")
        assert ride.status == RideStatus.ASSIGNED.value

        # Start pickup
        ride.start_pickup()
        assert ride.status == RideStatus.PICKUP.value

        # Start trip
        ride.start_trip()
        assert ride.status == RideStatus.ON_TRIP.value

        # Complete
        ride.complete()
        assert ride.status == RideStatus.COMPLETED.value

        # Test fail
        ride2 = RideRequest(
            id="ride9",
            rider_id="rider9",
            pickup_x=10,
            pickup_y=20,
            dropoff_x=80,
            dropoff_y=90
        )
        ride2.fail()
        assert ride2.status == RideStatus.FAILED.value


class TestEnums:
    """Test enum values"""

    def test_driver_status_enum(self):
        """Test DriverStatus enum values"""
        assert DriverStatus.AVAILABLE.value == "available"
        assert DriverStatus.ASSIGNED.value == "assigned"
        assert DriverStatus.ON_TRIP.value == "on_trip"
        assert DriverStatus.OFFLINE.value == "offline"

    def test_rider_status_enum(self):
        """Test RiderStatus enum values"""
        assert RiderStatus.WAITING.value == "waiting"
        assert RiderStatus.PICKED_UP.value == "picked_up"
        assert RiderStatus.COMPLETED.value == "completed"

    def test_ride_status_enum(self):
        """Test RideStatus enum values"""
        assert RideStatus.WAITING.value == "waiting"
        assert RideStatus.ASSIGNED.value == "assigned"
        assert RideStatus.PICKUP.value == "pickup"
        assert RideStatus.ON_TRIP.value == "on_trip"
        assert RideStatus.COMPLETED.value == "completed"
        assert RideStatus.FAILED.value == "failed"


if __name__ == "__main__":
    pytest.main([__file__])