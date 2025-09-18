"""
Geometry utilities for the ride dispatch simulation system
Provides Manhattan distance calculations and radius checks
"""


def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """
    Calculate Manhattan distance between two points on the grid
    Manhattan distance is the sum of absolute differences of coordinates

    Args:
        x1: X-coordinate of first point
        y1: Y-coordinate of first point
        x2: X-coordinate of second point
        y2: Y-coordinate of second point

    Returns:
        int: Manhattan distance between the two points

    Examples:
        >>> manhattan_distance(0, 0, 3, 4)
        7
        >>> manhattan_distance(10, 20, 15, 25)
        10
    """
    return abs(x1 - x2) + abs(y1 - y2)


def is_within_radius(center_x: int, center_y: int,
                     target_x: int, target_y: int,
                     radius: int) -> bool:
    """
    Check if a target point is within a given radius of a center point
    Uses Manhattan distance for the calculation

    Args:
        center_x: X-coordinate of center point
        center_y: Y-coordinate of center point
        target_x: X-coordinate of target point
        target_y: Y-coordinate of target point
        radius: Radius to check (in Manhattan distance units)

    Returns:
        bool: True if target is within radius of center, False otherwise

    Examples:
        >>> is_within_radius(50, 50, 55, 52, 10)
        True
        >>> is_within_radius(50, 50, 60, 60, 10)
        False
    """
    distance = manhattan_distance(center_x, center_y, target_x, target_y)
    return distance <= radius


def validate_coordinates(x: int, y: int, grid_size: int = 100) -> bool:
    """
    Validate that coordinates are within grid boundaries

    Args:
        x: X-coordinate to validate
        y: Y-coordinate to validate
        grid_size: Size of the grid (default: 100)

    Returns:
        bool: True if coordinates are valid, False otherwise
    """
    return 0 <= x < grid_size and 0 <= y < grid_size


def clamp_to_grid(x: int, y: int, grid_size: int = 100) -> tuple[int, int]:
    """
    Clamp coordinates to ensure they stay within grid boundaries

    Args:
        x: X-coordinate to clamp
        y: Y-coordinate to clamp
        grid_size: Size of the grid (default: 100)

    Returns:
        tuple[int, int]: Clamped (x, y) coordinates

    Examples:
        >>> clamp_to_grid(-5, 105, 100)
        (0, 99)
        >>> clamp_to_grid(50, 75, 100)
        (50, 75)
    """
    clamped_x = max(0, min(x, grid_size - 1))
    clamped_y = max(0, min(y, grid_size - 1))
    return clamped_x, clamped_y


def calculate_eta(from_x: int, from_y: int, to_x: int, to_y: int) -> int:
    """
    Calculate estimated time of arrival (ETA) between two points
    Assumes 1 tick per grid unit of Manhattan distance

    Args:
        from_x: Starting X-coordinate
        from_y: Starting Y-coordinate
        to_x: Destination X-coordinate
        to_y: Destination Y-coordinate

    Returns:
        int: ETA in ticks (equal to Manhattan distance)
    """
    return manhattan_distance(from_x, from_y, to_x, to_y)


def find_points_within_radius(center_x: int, center_y: int,
                              radius: int, grid_size: int = 100) -> list[tuple[int, int]]:
    """
    Find all grid points within a given radius of a center point
    Uses Manhattan distance

    Args:
        center_x: X-coordinate of center point
        center_y: Y-coordinate of center point
        radius: Radius to search within
        grid_size: Size of the grid (default: 100)

    Returns:
        list[tuple[int, int]]: List of (x, y) coordinates within radius

    Note:
        This function is useful for visualization but may be expensive
        for large radii. Use sparingly in performance-critical code.
    """
    points = []

    # Optimize search bounds to avoid checking entire grid
    min_x = max(0, center_x - radius)
    max_x = min(grid_size - 1, center_x + radius)
    min_y = max(0, center_y - radius)
    max_y = min(grid_size - 1, center_y + radius)

    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            if is_within_radius(center_x, center_y, x, y, radius):
                points.append((x, y))

    return points