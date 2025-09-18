"""
Unit tests for geometry utilities
"""
import pytest
from src.utils.geometry import (
    manhattan_distance,
    is_within_radius,
    validate_coordinates,
    clamp_to_grid,
    calculate_eta,
    find_points_within_radius
)


class TestManhattanDistance:
    """Test Manhattan distance calculation"""

    def test_same_point(self):
        """Distance between same point should be 0"""
        assert manhattan_distance(5, 5, 5, 5) == 0

    def test_horizontal_distance(self):
        """Test distance along horizontal axis"""
        assert manhattan_distance(0, 5, 10, 5) == 10
        assert manhattan_distance(10, 5, 0, 5) == 10

    def test_vertical_distance(self):
        """Test distance along vertical axis"""
        assert manhattan_distance(5, 0, 5, 10) == 10
        assert manhattan_distance(5, 10, 5, 0) == 10

    def test_diagonal_distance(self):
        """Test Manhattan distance for diagonal points"""
        assert manhattan_distance(0, 0, 3, 4) == 7
        assert manhattan_distance(10, 20, 15, 25) == 10

    def test_negative_coordinates(self):
        """Test with negative coordinates (edge case)"""
        assert manhattan_distance(-5, -5, 5, 5) == 20


class TestIsWithinRadius:
    """Test radius checking functionality"""

    def test_point_at_center(self):
        """Point at center is always within radius"""
        assert is_within_radius(50, 50, 50, 50, 1)
        assert is_within_radius(50, 50, 50, 50, 0)

    def test_point_within_radius(self):
        """Test points within radius"""
        assert is_within_radius(50, 50, 55, 52, 10)
        assert is_within_radius(0, 0, 3, 4, 7)

    def test_point_outside_radius(self):
        """Test points outside radius"""
        assert not is_within_radius(50, 50, 60, 60, 10)
        assert not is_within_radius(0, 0, 5, 5, 5)

    def test_point_on_radius_boundary(self):
        """Test points exactly on radius boundary"""
        assert is_within_radius(50, 50, 55, 55, 10)  # Distance = 10
        assert not is_within_radius(50, 50, 56, 55, 10)  # Distance = 11


class TestValidateCoordinates:
    """Test coordinate validation"""

    def test_valid_coordinates(self):
        """Test valid coordinates within grid"""
        assert validate_coordinates(0, 0)
        assert validate_coordinates(50, 50)
        assert validate_coordinates(99, 99)

    def test_invalid_coordinates(self):
        """Test invalid coordinates outside grid"""
        assert not validate_coordinates(-1, 50)
        assert not validate_coordinates(50, -1)
        assert not validate_coordinates(100, 50)
        assert not validate_coordinates(50, 100)

    def test_custom_grid_size(self):
        """Test with custom grid size"""
        assert validate_coordinates(49, 49, grid_size=50)
        assert not validate_coordinates(50, 50, grid_size=50)


class TestClampToGrid:
    """Test coordinate clamping"""

    def test_valid_coordinates_unchanged(self):
        """Valid coordinates should not be changed"""
        assert clamp_to_grid(50, 75) == (50, 75)
        assert clamp_to_grid(0, 99) == (0, 99)

    def test_clamp_negative_coordinates(self):
        """Negative coordinates should be clamped to 0"""
        assert clamp_to_grid(-5, 50) == (0, 50)
        assert clamp_to_grid(50, -10) == (50, 0)
        assert clamp_to_grid(-5, -10) == (0, 0)

    def test_clamp_overflow_coordinates(self):
        """Coordinates beyond grid should be clamped to max"""
        assert clamp_to_grid(105, 50) == (99, 50)
        assert clamp_to_grid(50, 200) == (50, 99)
        assert clamp_to_grid(150, 150) == (99, 99)

    def test_custom_grid_size(self):
        """Test clamping with custom grid size"""
        assert clamp_to_grid(60, 60, grid_size=50) == (49, 49)
        assert clamp_to_grid(-5, -5, grid_size=50) == (0, 0)


class TestCalculateEta:
    """Test ETA calculation"""

    def test_same_location(self):
        """ETA to same location should be 0"""
        assert calculate_eta(50, 50, 50, 50) == 0

    def test_eta_calculation(self):
        """Test ETA equals Manhattan distance"""
        assert calculate_eta(0, 0, 10, 10) == 20
        assert calculate_eta(25, 25, 30, 35) == 15
        assert calculate_eta(99, 99, 0, 0) == 198


class TestFindPointsWithinRadius:
    """Test finding points within radius"""

    def test_radius_zero(self):
        """Radius 0 should only return center point"""
        points = find_points_within_radius(50, 50, 0)
        assert len(points) == 1
        assert (50, 50) in points

    def test_small_radius(self):
        """Test with small radius"""
        points = find_points_within_radius(50, 50, 2)
        # Should include center and points with Manhattan distance <= 2
        assert (50, 50) in points
        assert (51, 50) in points
        assert (49, 50) in points
        assert (50, 51) in points
        assert (50, 49) in points
        assert (51, 51) in points
        # Should not include points with distance > 2
        assert (52, 51) not in points

    def test_boundary_clamping(self):
        """Test that points are clamped to grid boundaries"""
        points = find_points_within_radius(0, 0, 5)
        for x, y in points:
            assert x >= 0 and y >= 0

        points = find_points_within_radius(99, 99, 5)
        for x, y in points:
            assert x <= 99 and y <= 99

    def test_custom_grid_size(self):
        """Test with custom grid size"""
        points = find_points_within_radius(25, 25, 3, grid_size=50)
        for x, y in points:
            assert 0 <= x < 50 and 0 <= y < 50


if __name__ == "__main__":
    pytest.main([__file__])