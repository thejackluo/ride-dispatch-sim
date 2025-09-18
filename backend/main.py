"""
Ride Dispatch Simulator API
Main FastAPI application with CORS configuration for frontend communication
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
import logging

from src.state import simulation_state
from src.models import Driver, Rider, RideRequest, DriverStatus
from src.algorithms import (
    dispatch_ride,
    auto_process_acceptance,
    process_all_driver_movements,
    batch_dispatch
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ride Dispatch Simulator API",
    description="Backend API for ride-hailing simulation system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class DriverCreate(BaseModel):
    """Request model for creating a driver"""
    x: int
    y: int
    id: Optional[str] = None


class RiderCreate(BaseModel):
    """Request model for creating a rider"""
    x: int
    y: int
    id: Optional[str] = None


class RideRequestCreate(BaseModel):
    """Request model for creating a ride request"""
    rider_id: str
    pickup_x: int
    pickup_y: int
    dropoff_x: int
    dropoff_y: int


class ConfigUpdate(BaseModel):
    """Request model for updating configuration"""
    fairness_penalty: Optional[float] = None
    initial_search_radius: Optional[int] = None
    max_search_radius: Optional[int] = None
    radius_growth_interval: Optional[int] = None
    rejection_cooldown_ticks: Optional[int] = None


@app.get("/")
def read_root():
    """
    Root endpoint returning API status and basic information

    Returns:
        dict: API status message and version
    """
    return {
        "message": "Ride Dispatch Simulator API",
        "status": "operational",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring API availability

    Returns:
        dict: Health status
    """
    return {"status": "healthy"}


@app.get("/state")
def get_state():
    """
    Get complete simulation state

    Returns:
        dict: Complete state including drivers, riders, rides, and configuration
    """
    return simulation_state.to_dict()


@app.post("/reset")
def reset_simulation():
    """
    Reset the simulation to initial empty state

    Returns:
        dict: Success message
    """
    simulation_state.reset()
    logger.info("Simulation reset")
    return {"message": "Simulation reset successfully"}


@app.post("/drivers")
def create_driver(driver_data: DriverCreate):
    """
    Create a new driver in the simulation

    Args:
        driver_data: Driver creation parameters

    Returns:
        dict: Created driver data

    Raises:
        HTTPException: If driver ID already exists
    """
    driver_id = driver_data.id or f"driver_{uuid.uuid4().hex[:8]}"

    try:
        driver = Driver(
            id=driver_id,
            x=driver_data.x,
            y=driver_data.y
        )
        simulation_state.add_driver(driver)
        logger.info(f"Created driver {driver_id} at ({driver.x}, {driver.y})")
        return driver.dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/riders")
def create_rider(rider_data: RiderCreate):
    """
    Create a new rider in the simulation

    Args:
        rider_data: Rider creation parameters

    Returns:
        dict: Created rider data

    Raises:
        HTTPException: If rider ID already exists
    """
    rider_id = rider_data.id or f"rider_{uuid.uuid4().hex[:8]}"

    try:
        rider = Rider(
            id=rider_id,
            x=rider_data.x,
            y=rider_data.y
        )
        simulation_state.add_rider(rider)
        logger.info(f"Created rider {rider_id} at ({rider.x}, {rider.y})")
        return rider.dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/rides")
def request_ride(ride_data: RideRequestCreate):
    """
    Create a new ride request

    Args:
        ride_data: Ride request parameters

    Returns:
        dict: Created ride request data with dispatch result

    Raises:
        HTTPException: If rider doesn't exist or invalid coordinates
    """
    # Verify rider exists
    rider = simulation_state.get_rider(ride_data.rider_id)
    if not rider:
        raise HTTPException(status_code=404, detail=f"Rider {ride_data.rider_id} not found")

    ride_id = f"ride_{uuid.uuid4().hex[:8]}"

    try:
        ride = RideRequest(
            id=ride_id,
            rider_id=ride_data.rider_id,
            pickup_x=ride_data.pickup_x,
            pickup_y=ride_data.pickup_y,
            dropoff_x=ride_data.dropoff_x,
            dropoff_y=ride_data.dropoff_y
        )
        simulation_state.add_ride_request(ride)
        logger.info(f"Created ride request {ride_id}")

        # Attempt immediate dispatch
        success, driver_id = dispatch_ride(ride_id, simulation_state)

        if success and driver_id:
            # Process driver acceptance
            accepted = auto_process_acceptance(driver_id, ride_id, simulation_state)
            logger.info(f"Ride {ride_id} dispatch result: driver={driver_id}, accepted={accepted}")

        return {
            "ride": ride.dict(),
            "dispatched": success,
            "assigned_driver_id": driver_id
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/tick")
def advance_tick():
    """
    Advance simulation by one tick
    Processes driver movement, ride progression, and new dispatches

    Returns:
        dict: Summary of tick processing results
    """
    simulation_state.increment_tick()
    tick = simulation_state.current_tick

    # Process driver movements and ride progression
    process_all_driver_movements(simulation_state)

    # Attempt to dispatch waiting rides
    dispatched = batch_dispatch(simulation_state)

    # Process acceptances for newly dispatched rides
    for ride_id, driver_id in dispatched.items():
        auto_process_acceptance(driver_id, ride_id, simulation_state)

    summary = simulation_state.get_state_summary()
    logger.info(f"Tick {tick} processed: {len(dispatched)} rides dispatched")

    return {
        "tick": tick,
        "rides_dispatched": len(dispatched),
        "summary": summary
    }


@app.put("/config")
def update_config(config_data: ConfigUpdate):
    """
    Update simulation configuration parameters

    Args:
        config_data: Configuration parameters to update

    Returns:
        dict: Updated configuration
    """
    updates = config_data.dict(exclude_unset=True)

    try:
        simulation_state.update_config(updates)
        logger.info(f"Configuration updated: {updates}")

        return {
            "message": "Configuration updated successfully",
            "config": {
                "initial_search_radius": simulation_state.config.initial_search_radius,
                "max_search_radius": simulation_state.config.max_search_radius,
                "radius_growth_interval": simulation_state.config.radius_growth_interval,
                "rejection_cooldown_ticks": simulation_state.config.rejection_cooldown_ticks,
                "fairness_penalty": simulation_state.config.fairness_penalty
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/drivers/{driver_id}")
def remove_driver(driver_id: str):
    """
    Remove a driver from the simulation

    Args:
        driver_id: ID of driver to remove

    Returns:
        dict: Success message

    Raises:
        HTTPException: If driver not found or currently on trip
    """
    driver = simulation_state.get_driver(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail=f"Driver {driver_id} not found")

    if driver.status != DriverStatus.AVAILABLE:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot remove driver {driver_id} - currently {driver.status}"
        )

    del simulation_state.drivers[driver_id]
    logger.info(f"Removed driver {driver_id}")

    return {"message": f"Driver {driver_id} removed successfully"}


@app.delete("/riders/{rider_id}")
def remove_rider(rider_id: str):
    """
    Remove a rider from the simulation

    Args:
        rider_id: ID of rider to remove

    Returns:
        dict: Success message

    Raises:
        HTTPException: If rider not found
    """
    rider = simulation_state.get_rider(rider_id)
    if not rider:
        raise HTTPException(status_code=404, detail=f"Rider {rider_id} not found")

    del simulation_state.riders[rider_id]
    logger.info(f"Removed rider {rider_id}")

    return {"message": f"Rider {rider_id} removed successfully"}