import { useState, useEffect } from 'react'
import './App.css'

interface Driver {
  id: string
  x: number
  y: number
  status: 'available' | 'on_trip' | 'offline'
  completedRides: number
  searchRadius: number
}

interface Rider {
  id: string
  x: number
  y: number
  status: 'waiting' | 'picked_up' | 'completed'
}

interface RideRequest {
  id: string
  riderId: string
  pickupX: number
  pickupY: number
  dropoffX: number
  dropoffY: number
  status: 'waiting' | 'assigned' | 'in_progress' | 'completed' | 'failed'
  driverId?: string
  eta?: number
}

interface SimState {
  drivers: Record<string, Driver>
  riders: Record<string, Rider>
  rides: RideRequest[]
  tick: number
  fairnessPenalty: number
}

function App() {
  const [state, setState] = useState<SimState>({
    drivers: {
      'driver_1': { id: 'driver_1', x: 20, y: 30, status: 'available', completedRides: 0, searchRadius: 5 },
      'driver_2': { id: 'driver_2', x: 70, y: 80, status: 'available', completedRides: 0, searchRadius: 5 },
    },
    riders: {
      'rider_1': { id: 'rider_1', x: 40, y: 50, status: 'waiting' },
    },
    rides: [],
    tick: 0,
    fairnessPenalty: 1.0
  })

  const [isManualMode, setIsManualMode] = useState(false)
  const [manualX, setManualX] = useState('')
  const [manualY, setManualY] = useState('')
  const [dropoffX, setDropoffX] = useState('')
  const [dropoffY, setDropoffY] = useState('')

  const manhattanDistance = (x1: number, y1: number, x2: number, y2: number) => {
    return Math.abs(x1 - x2) + Math.abs(y1 - y2)
  }

  const addDriver = () => {
    const id = `driver_${Date.now()}`
    let x: number, y: number

    if (isManualMode && manualX && manualY) {
      x = Math.min(99, Math.max(0, parseInt(manualX)))
      y = Math.min(99, Math.max(0, parseInt(manualY)))
    } else {
      x = Math.floor(Math.random() * 100)
      y = Math.floor(Math.random() * 100)
    }

    setState(prev => ({
      ...prev,
      drivers: {
        ...prev.drivers,
        [id]: { id, x, y, status: 'available', completedRides: 0, searchRadius: 5 }
      }
    }))
    setManualX('')
    setManualY('')
  }

  const addRider = () => {
    const id = `rider_${Date.now()}`
    let x: number, y: number

    if (isManualMode && manualX && manualY) {
      x = Math.min(99, Math.max(0, parseInt(manualX)))
      y = Math.min(99, Math.max(0, parseInt(manualY)))
    } else {
      x = Math.floor(Math.random() * 100)
      y = Math.floor(Math.random() * 100)
    }

    setState(prev => ({
      ...prev,
      riders: {
        ...prev.riders,
        [id]: { id, x, y, status: 'waiting' }
      }
    }))
    setManualX('')
    setManualY('')
  }

  const requestRide = (riderId: string) => {
    const rider = state.riders[riderId]
    if (!rider || rider.status !== 'waiting') {
      return
    }

    const rideId = `ride_${Date.now()}`
    let destX: number, destY: number

    if (isManualMode && dropoffX && dropoffY) {
      destX = Math.min(99, Math.max(0, parseInt(dropoffX)))
      destY = Math.min(99, Math.max(0, parseInt(dropoffY)))
    } else {
      destX = Math.floor(Math.random() * 100)
      destY = Math.floor(Math.random() * 100)
    }

    const newRide: RideRequest = {
      id: rideId,
      riderId: rider.id,
      pickupX: rider.x,
      pickupY: rider.y,
      dropoffX: destX,
      dropoffY: destY,
      status: 'waiting'
    }

    const availableDrivers = Object.values(state.drivers).filter(d => d.status === 'available')

    if (availableDrivers.length > 0) {
      const sortedDrivers = availableDrivers
        .map(driver => ({
          driver,
          distance: manhattanDistance(driver.x, driver.y, rider.x, rider.y),
          fairnessScore: driver.completedRides * state.fairnessPenalty
        }))
        .sort((a, b) => {
          if (a.fairnessScore !== b.fairnessScore) {
            return a.fairnessScore - b.fairnessScore
          }
          return a.distance - b.distance
        })

      const selectedDriver = sortedDrivers[0].driver
      const eta = sortedDrivers[0].distance

      newRide.status = 'assigned'
      newRide.driverId = selectedDriver.id
      newRide.eta = eta

      setState(prev => ({
        ...prev,
        drivers: {
          ...prev.drivers,
          [selectedDriver.id]: { ...selectedDriver, status: 'on_trip' }
        },
        riders: {
          ...prev.riders,
          [rider.id]: { ...rider, status: 'picked_up' }
        },
        rides: [...prev.rides, newRide]
      }))
    } else {
      newRide.status = 'failed'
      setState(prev => ({
        ...prev,
        rides: [...prev.rides, newRide]
      }))
    }
    setDropoffX('')
    setDropoffY('')
  }

  const nextTick = () => {
    setState(prev => {
      const newState = { ...prev, tick: prev.tick + 1 }
      const updatedDrivers = { ...prev.drivers }
      const updatedRiders = { ...prev.riders }
      const updatedRides = [...prev.rides]

      updatedRides.forEach((ride, index) => {
        if (ride.status === 'assigned' && ride.driverId) {
          const driver = updatedDrivers[ride.driverId]
          const rider = updatedRiders[ride.riderId]

          if (driver && rider) {
            const toPickup = manhattanDistance(driver.x, driver.y, ride.pickupX, ride.pickupY)

            if (toPickup > 0) {
              const dx = ride.pickupX > driver.x ? 1 : ride.pickupX < driver.x ? -1 : 0
              const dy = ride.pickupY > driver.y ? 1 : ride.pickupY < driver.y ? -1 : 0

              if (dx !== 0) {
                driver.x += dx
              } else if (dy !== 0) {
                driver.y += dy
              }
              updatedDrivers[driver.id] = driver
            } else {
              updatedRides[index] = { ...ride, status: 'in_progress' }
              rider.status = 'picked_up'
              updatedRiders[rider.id] = rider
            }
          }
        } else if (ride.status === 'in_progress' && ride.driverId) {
          const driver = updatedDrivers[ride.driverId]

          if (driver) {
            const toDropoff = manhattanDistance(driver.x, driver.y, ride.dropoffX, ride.dropoffY)

            if (toDropoff > 0) {
              const dx = ride.dropoffX > driver.x ? 1 : ride.dropoffX < driver.x ? -1 : 0
              const dy = ride.dropoffY > driver.y ? 1 : ride.dropoffY < driver.y ? -1 : 0

              if (dx !== 0) {
                driver.x += dx
              } else if (dy !== 0) {
                driver.y += dy
              }
              updatedDrivers[driver.id] = driver
            } else {
              updatedRides[index] = { ...ride, status: 'completed' }
              driver.status = 'available'
              driver.completedRides += 1
              updatedDrivers[driver.id] = driver

              const rider = updatedRiders[ride.riderId]
              if (rider) {
                rider.status = 'completed'
                rider.x = ride.dropoffX
                rider.y = ride.dropoffY
                updatedRiders[rider.id] = rider
              }
            }
          }
        }
      })

      return {
        ...newState,
        drivers: updatedDrivers,
        riders: updatedRiders,
        rides: updatedRides
      }
    })
  }

  const getEntityAtPosition = (x: number, y: number) => {
    const drivers = Object.values(state.drivers).filter(d => d.x === x && d.y === y)
    const riders = Object.values(state.riders).filter(r => r.x === x && r.y === y && r.status !== 'completed')
    return { drivers, riders }
  }

  return (
    <div className="App" style={{ padding: '20px', fontFamily: 'monospace' }}>
      <header>
        <h1>🛺 Ride Dispatch Simulator</h1>
        <p style={{ color: '#666' }}>Tick: {state.tick} | Fairness Penalty: {state.fairnessPenalty}</p>
      </header>

      <main style={{ display: 'flex', gap: '20px', marginTop: '20px', flexWrap: 'wrap' }}>
        <div style={{ minWidth: '300px' }}>
          <section className="controls" style={{ marginBottom: '20px' }}>
            <h3>Controls</h3>

            <div style={{ marginBottom: '15px', padding: '10px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <input
                  type="checkbox"
                  checked={isManualMode}
                  onChange={e => setIsManualMode(e.target.checked)}
                />
                <span>Manual Position Mode</span>
              </label>

              {isManualMode && (
                <div style={{ marginTop: '10px' }}>
                  <div style={{ marginBottom: '10px' }}>
                    <strong>Position (0-99):</strong>
                    <div style={{ display: 'flex', gap: '10px', marginTop: '5px' }}>
                      <input
                        type="number"
                        placeholder="X"
                        value={manualX}
                        onChange={e => setManualX(e.target.value)}
                        style={{ width: '60px', padding: '4px' }}
                        min="0"
                        max="99"
                      />
                      <input
                        type="number"
                        placeholder="Y"
                        value={manualY}
                        onChange={e => setManualY(e.target.value)}
                        style={{ width: '60px', padding: '4px' }}
                        min="0"
                        max="99"
                      />
                    </div>
                  </div>

                  <div>
                    <strong>Dropoff (for rides):</strong>
                    <div style={{ display: 'flex', gap: '10px', marginTop: '5px' }}>
                      <input
                        type="number"
                        placeholder="X"
                        value={dropoffX}
                        onChange={e => setDropoffX(e.target.value)}
                        style={{ width: '60px', padding: '4px' }}
                        min="0"
                        max="99"
                      />
                      <input
                        type="number"
                        placeholder="Y"
                        value={dropoffY}
                        onChange={e => setDropoffY(e.target.value)}
                        style={{ width: '60px', padding: '4px' }}
                        min="0"
                        max="99"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button onClick={addDriver} style={{ padding: '8px 16px', cursor: 'pointer', backgroundColor: '#4CAF50', color: 'white', border: 'none', borderRadius: '4px' }}>
                Add Driver {isManualMode ? '(Manual)' : '(Random)'}
              </button>
              <button onClick={addRider} style={{ padding: '8px 16px', cursor: 'pointer', backgroundColor: '#2196F3', color: 'white', border: 'none', borderRadius: '4px' }}>
                Add Rider {isManualMode ? '(Manual)' : '(Random)'}
              </button>
              <button onClick={nextTick} style={{ padding: '8px 16px', cursor: 'pointer', backgroundColor: '#9C27B0', color: 'white', border: 'none', borderRadius: '4px' }}>
                Next Tick ⏭
              </button>
            </div>
            <div style={{ marginTop: '10px' }}>
              <label>Fairness Penalty: </label>
              <input
                type="number"
                value={state.fairnessPenalty}
                onChange={e => setState(prev => ({ ...prev, fairnessPenalty: parseFloat(e.target.value) || 1 }))}
                style={{ width: '60px', marginLeft: '10px' }}
                step="0.1"
              />
            </div>
          </section>

          <section className="grid-container" style={{ flex: 1 }}>
            <h3>City Grid (100x100)</h3>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(100, 8px)',
              gap: '0',
              backgroundColor: '#f0f0f0',
              padding: '2px',
              maxWidth: '820px',
              overflow: 'auto'
            }}>
              {Array.from({ length: 10000 }, (_, i) => {
                const x = i % 100
                const y = Math.floor(i / 100)
                const { drivers, riders } = getEntityAtPosition(x, y)

                const hasAvailableDriver = drivers.some(d => d.status === 'available')
                const hasOnTripDriver = drivers.some(d => d.status === 'on_trip')
                const hasRider = riders.length > 0

                return (
                  <div
                    key={i}
                    style={{
                      width: '8px',
                      height: '8px',
                      backgroundColor: hasOnTripDriver ? '#FFA500' : hasAvailableDriver ? '#4CAF50' : hasRider ? '#F44336' : 'white',
                      border: hasOnTripDriver || hasAvailableDriver || hasRider ? '1px solid rgba(0,0,0,0.3)' : '1px solid #f5f5f5',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '6px',
                      fontWeight: 'bold',
                      cursor: 'pointer',
                      position: 'relative'
                    }}
                    title={`(${x}, ${y})${hasAvailableDriver ? ' - Driver (available)' : ''}${hasOnTripDriver ? ' - Driver (on trip)' : ''}${hasRider ? ' - Rider' : ''}`}
                  >
                  </div>
                )
              })}
            </div>
            <div style={{ marginTop: '10px', fontSize: '12px' }}>
              <span style={{ display: 'inline-block', width: '15px', height: '10px', backgroundColor: '#4CAF50', marginRight: '5px' }}></span> Available Driver
              <span style={{ display: 'inline-block', width: '15px', height: '10px', backgroundColor: '#FFA500', marginLeft: '10px', marginRight: '5px' }}></span> Driver On Trip
              <span style={{ display: 'inline-block', width: '15px', height: '10px', backgroundColor: '#F44336', marginLeft: '10px', marginRight: '5px' }}></span> Rider
              <span style={{ marginLeft: '20px', color: '#666' }}>Hover over cells for coordinates</span>
            </div>
          </section>
        </div>

        <div style={{ minWidth: '400px' }}>
          <section className="status">
            <h3>Riders ({Object.keys(state.riders).length})</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f5f5f5' }}>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>ID</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Position</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Status</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {Object.values(state.riders).map(rider => (
                  <tr key={rider.id}>
                    <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>{rider.id}</td>
                    <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>({rider.x}, {rider.y})</td>
                    <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>
                      <span style={{
                        color: rider.status === 'waiting' ? 'orange' : rider.status === 'picked_up' ? 'blue' : 'green'
                      }}>
                        {rider.status}
                      </span>
                    </td>
                    <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>
                      {rider.status === 'waiting' && (
                        <button
                          onClick={() => requestRide(rider.id)}
                          style={{
                            padding: '4px 8px',
                            fontSize: '12px',
                            backgroundColor: '#FF9800',
                            color: 'white',
                            border: 'none',
                            borderRadius: '3px',
                            cursor: 'pointer'
                          }}
                        >
                          Request Ride
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <h3 style={{ marginTop: '20px' }}>Drivers ({Object.keys(state.drivers).length})</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f5f5f5' }}>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>ID</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Position</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Status</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Rides</th>
                </tr>
              </thead>
              <tbody>
                {Object.values(state.drivers).map(driver => (
                  <tr key={driver.id}>
                    <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>{driver.id}</td>
                    <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>({driver.x}, {driver.y})</td>
                    <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>
                      <span style={{
                        color: driver.status === 'available' ? 'green' : driver.status === 'on_trip' ? 'orange' : 'gray'
                      }}>
                        {driver.status}
                      </span>
                    </td>
                    <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>{driver.completedRides}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <h3 style={{ marginTop: '20px' }}>Active Rides ({state.rides.filter(r => r.status !== 'completed' && r.status !== 'failed').length})</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f5f5f5' }}>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>ID</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Status</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Pickup</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Dropoff</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Driver</th>
                </tr>
              </thead>
              <tbody>
                {state.rides
                  .filter(ride => ride.status !== 'completed' && ride.status !== 'failed')
                  .map(ride => (
                    <tr key={ride.id}>
                      <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>{ride.id}</td>
                      <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>
                        <span style={{
                          color: ride.status === 'waiting' ? 'orange' : ride.status === 'assigned' ? 'blue' : 'green'
                        }}>
                          {ride.status}
                        </span>
                      </td>
                      <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>({ride.pickupX}, {ride.pickupY})</td>
                      <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>({ride.dropoffX}, {ride.dropoffY})</td>
                      <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>{ride.driverId || '-'}</td>
                    </tr>
                  ))}
              </tbody>
            </table>

            <h3 style={{ marginTop: '20px' }}>Statistics</h3>
            <div style={{ fontSize: '14px' }}>
              <p>Total Drivers: {Object.keys(state.drivers).length}</p>
              <p>Available Drivers: {Object.values(state.drivers).filter(d => d.status === 'available').length}</p>
              <p>Total Riders: {Object.keys(state.riders).length}</p>
              <p>Waiting Riders: {Object.values(state.riders).filter(r => r.status === 'waiting').length}</p>
              <p>Completed Rides: {state.rides.filter(r => r.status === 'completed').length}</p>
              <p>Failed Rides: {state.rides.filter(r => r.status === 'failed').length}</p>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}

export default App
