import { useState, useEffect } from 'react'
import './App.css'

const API_BASE_URL = 'http://localhost:8000'

interface Driver {
  id: string
  x: number
  y: number
  status: 'available' | 'assigned' | 'on_trip' | 'offline'
  completed_rides: number
  search_radius: number
  idle_ticks: number
  current_ride_id?: string
}

interface Rider {
  id: string
  x: number
  y: number
  status: 'waiting' | 'picked_up' | 'completed'
}

interface RideRequest {
  id: string
  rider_id: string
  pickup_x: number
  pickup_y: number
  dropoff_x: number
  dropoff_y: number
  status: 'waiting' | 'assigned' | 'pickup' | 'on_trip' | 'completed' | 'failed'
  assigned_driver_id?: string
  rejected_driver_ids: string[]
  created_tick: number
  cooldown_until_tick?: number
}

interface SimState {
  current_tick: number
  config: {
    initial_search_radius: number
    max_search_radius: number
    radius_growth_interval: number
    grid_size: number
    rejection_cooldown_ticks: number
    fairness_penalty: number
  }
  drivers: Record<string, Driver>
  riders: Record<string, Rider>
  ride_requests: Record<string, RideRequest>
  summary?: any
}

interface HoverInfo {
  type: 'driver' | 'rider' | 'pickup' | 'dropoff' | null
  id?: string
  path?: { x1: number, y1: number, x2: number, y2: number }
}

function App() {
  const [state, setState] = useState<SimState | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [isManualMode, setIsManualMode] = useState(false)
  const [manualX, setManualX] = useState('')
  const [manualY, setManualY] = useState('')
  const [dropoffX, setDropoffX] = useState('')
  const [dropoffY, setDropoffY] = useState('')
  const [hoveredCell, setHoveredCell] = useState<{ x: number, y: number } | null>(null)

  // Fetch state from backend
  const fetchState = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/state`)
      if (!response.ok) throw new Error('Failed to fetch state')
      const data = await response.json()
      setState(data)
      setLoading(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch state')
      setLoading(false)
    }
  }

  // Poll state every 2 seconds
  useEffect(() => {
    fetchState()
    const interval = setInterval(fetchState, 2000)
    return () => clearInterval(interval)
  }, [])

  const manhattanDistance = (x1: number, y1: number, x2: number, y2: number) => {
    return Math.abs(x1 - x2) + Math.abs(y1 - y2)
  }

  const addDriver = async () => {
    let x: number, y: number

    if (isManualMode && manualX && manualY) {
      x = Math.min(99, Math.max(0, parseInt(manualX)))
      y = Math.min(99, Math.max(0, parseInt(manualY)))
    } else {
      x = Math.floor(Math.random() * 100)
      y = Math.floor(Math.random() * 100)
    }

    try {
      const response = await fetch(`${API_BASE_URL}/drivers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x, y })
      })
      if (!response.ok) throw new Error('Failed to add driver')
      await fetchState() // Refresh state
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add driver')
    }
    setManualX('')
    setManualY('')
  }

  const addRider = async () => {
    let x: number, y: number

    if (isManualMode && manualX && manualY) {
      x = Math.min(99, Math.max(0, parseInt(manualX)))
      y = Math.min(99, Math.max(0, parseInt(manualY)))
    } else {
      x = Math.floor(Math.random() * 100)
      y = Math.floor(Math.random() * 100)
    }

    try {
      const response = await fetch(`${API_BASE_URL}/riders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x, y })
      })
      if (!response.ok) throw new Error('Failed to add rider')
      await fetchState() // Refresh state
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add rider')
    }
    setManualX('')
    setManualY('')
  }

  const requestRide = async (riderId: string) => {
    if (!state) return
    const rider = state.riders[riderId]
    if (!rider || rider.status !== 'waiting') {
      return
    }

    let destX: number, destY: number

    if (isManualMode && dropoffX && dropoffY) {
      destX = Math.min(99, Math.max(0, parseInt(dropoffX)))
      destY = Math.min(99, Math.max(0, parseInt(dropoffY)))
    } else {
      destX = Math.floor(Math.random() * 100)
      destY = Math.floor(Math.random() * 100)
    }

    try {
      const response = await fetch(`${API_BASE_URL}/rides`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rider_id: riderId,
          pickup_x: rider.x,
          pickup_y: rider.y,
          dropoff_x: destX,
          dropoff_y: destY
        })
      })
      if (!response.ok) throw new Error('Failed to request ride')
      await fetchState() // Refresh state
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to request ride')
    }
    setDropoffX('')
    setDropoffY('')
  }

  const nextTick = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/tick`, {
        method: 'POST'
      })
      if (!response.ok) throw new Error('Failed to advance tick')
      await fetchState() // Refresh state
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to advance tick')
    }
  }

  const getEntityAtPosition = (x: number, y: number) => {
    if (!state) return { drivers: [], riders: [] }
    const drivers = Object.values(state.drivers).filter(d => d.x === x && d.y === y)
    const riders = Object.values(state.riders).filter(r => r.x === x && r.y === y)
    return { drivers, riders }
  }

  const getPathForCell = (x: number, y: number) => {
    const paths: HoverInfo[] = []
    if (!state) return paths

    // Check for drivers at this position
    const driversHere = Object.values(state.drivers).filter(d => d.x === x && d.y === y)
    driversHere.forEach(driver => {
      const activeRide = Object.values(state.ride_requests).find(
        r => r.assigned_driver_id === driver.id &&
        (r.status === 'assigned' || r.status === 'pickup' || r.status === 'on_trip')
      )
      if (activeRide) {
        if (activeRide.status === 'assigned' || activeRide.status === 'pickup') {
          // Path to pickup
          paths.push({
            type: 'driver',
            id: driver.id,
            path: { x1: driver.x, y1: driver.y, x2: activeRide.pickup_x, y2: activeRide.pickup_y }
          })
        } else if (activeRide.status === 'on_trip') {
          // Path to dropoff
          paths.push({
            type: 'driver',
            id: driver.id,
            path: { x1: driver.x, y1: driver.y, x2: activeRide.dropoff_x, y2: activeRide.dropoff_y }
          })
        }
      }
    })

    // Check for riders at this position
    const ridersHere = Object.values(state.riders).filter(r => r.x === x && r.y === y)
    ridersHere.forEach(rider => {
      const activeRide = Object.values(state.ride_requests).find(
        r => r.rider_id === rider.id &&
        (r.status === 'assigned' || r.status === 'pickup' || r.status === 'on_trip')
      )
      if (activeRide) {
        paths.push({
          type: 'rider',
          id: rider.id,
          path: { x1: activeRide.pickup_x, y1: activeRide.pickup_y, x2: activeRide.dropoff_x, y2: activeRide.dropoff_y }
        })
      }
    })

    return paths
  }

  const getCellStyle = (x: number, y: number, hasAvailableDriver: boolean, hasOnTripDriver: boolean, hasRider: boolean) => {
    if (!state) return { backgroundColor: 'white', width: '8px', height: '8px' }

    const paths = hoveredCell ? getPathForCell(hoveredCell.x, hoveredCell.y) : []

    let isOnPath = false
    let isPickup = false
    let isDropoff = false
    let isHoveredEntity = false

    // Check if we're hovering over an entity
    if (hoveredCell) {
      if (x === hoveredCell.x && y === hoveredCell.y) {
        isHoveredEntity = true
      }

      paths.forEach(pathInfo => {
        if (pathInfo.path) {
          const { x1, y1, x2, y2 } = pathInfo.path

          // For riders, show the entire trip path
          if (pathInfo.type === 'rider') {
            const ride = Object.values(state.ride_requests).find(
              r => r.rider_id === pathInfo.id &&
              (r.status === 'assigned' || r.status === 'pickup' || r.status === 'on_trip')
            )
            if (ride) {
              // Mark pickup and dropoff
              if (x === ride.pickup_x && y === ride.pickup_y) isPickup = true
              if (x === ride.dropoff_x && y === ride.dropoff_y) isDropoff = true

              // Show path from pickup to dropoff
              if (isOnManhattanPath(x, y, ride.pickup_x, ride.pickup_y, ride.dropoff_x, ride.dropoff_y)) {
                isOnPath = true
              }
            }
          }

          // For drivers, show path to current destination
          if (pathInfo.type === 'driver') {
            const ride = Object.values(state.ride_requests).find(
              r => r.assigned_driver_id === pathInfo.id &&
              (r.status === 'assigned' || r.status === 'pickup' || r.status === 'on_trip')
            )
            if (ride) {
              if (ride.status === 'assigned' || ride.status === 'pickup') {
                // Going to pickup
                if (x === ride.pickup_x && y === ride.pickup_y) isPickup = true
                if (isOnManhattanPath(x, y, x1, y1, x2, y2)) {
                  isOnPath = true
                }
              } else if (ride.status === 'on_trip') {
                // Going to dropoff
                if (x === ride.dropoff_x && y === ride.dropoff_y) isDropoff = true
                if (isOnManhattanPath(x, y, x1, y1, x2, y2)) {
                  isOnPath = true
                }
              }
            }
          }
        }
      })
    }

    // Check if this cell has a driver with a rider (picked up)
    const driversHere = Object.values(state.drivers).filter(d => d.x === x && d.y === y)
    const hasDriverWithRider = driversHere.some(driver => {
      const ride = Object.values(state.ride_requests).find(
        r => r.assigned_driver_id === driver.id && r.status === 'on_trip'
      )
      if (ride) {
        const rider = state.riders[ride.rider_id]
        return rider && rider.status === 'picked_up'
      }
      return false
    })

    let backgroundColor = 'white'
    if (hasDriverWithRider) backgroundColor = '#FF6B35' // Orange-red for driver with rider
    else if (hasOnTripDriver) backgroundColor = '#FFA500'
    else if (hasAvailableDriver) backgroundColor = '#4CAF50'
    else if (hasRider) backgroundColor = '#F44336'
    else if (isPickup) backgroundColor = '#2196F3'
    else if (isDropoff) backgroundColor = '#9C27B0'
    else if (isOnPath) backgroundColor = '#FFE082'

    return {
      width: '8px',
      height: '8px',
      backgroundColor,
      border: isHoveredEntity ? '2px solid #000' : (hasOnTripDriver || hasAvailableDriver || hasRider || isPickup || isDropoff || isOnPath) ? '1px solid rgba(0,0,0,0.3)' : '1px solid #f5f5f5',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '6px',
      fontWeight: 'bold',
      cursor: 'pointer',
      position: 'relative' as const,
      boxSizing: 'border-box' as const
    }
  }

  const isOnManhattanPath = (cellX: number, cellY: number, startX: number, startY: number, endX: number, endY: number) => {
    // Manhattan path: go horizontally first, then vertically (or vice versa)
    const onHorizontalPath = cellY === startY && cellX >= Math.min(startX, endX) && cellX <= Math.max(startX, endX)
    const onVerticalPath = cellX === endX && cellY >= Math.min(startY, endY) && cellY <= Math.max(startY, endY)
    return onHorizontalPath || onVerticalPath
  }

  const resetSimulation = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/reset`, {
        method: 'POST'
      })
      if (!response.ok) throw new Error('Failed to reset simulation')
      await fetchState() // Refresh state
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset simulation')
    }
  }

  if (loading) {
    return (
      <div style={{ padding: '20px', fontFamily: 'monospace' }}>
        <h1>🛺 Ride Dispatch Simulator</h1>
        <p>Loading...</p>
      </div>
    )
  }

  if (!state) {
    return (
      <div style={{ padding: '20px', fontFamily: 'monospace' }}>
        <h1>🛺 Ride Dispatch Simulator</h1>
        <p>Error: Failed to connect to backend. Make sure the backend is running on port 8000.</p>
      </div>
    )
  }

  return (
    <div className="App" style={{ padding: '20px', fontFamily: 'monospace' }}>
      <header>
        <h1>🛺 Ride Dispatch Simulator</h1>
        <p style={{ color: '#666' }}>Tick: {state.current_tick} | Fairness Penalty: {state.config.fairness_penalty}</p>
        {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      </header>

      <main style={{ display: 'flex', gap: '20px', marginTop: '20px' }}>
        <div style={{ minWidth: '300px', flexShrink: 0 }}>
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
                value={state.config.fairness_penalty}
                onChange={async (e) => {
                  const value = parseFloat(e.target.value) || 1
                  try {
                    const response = await fetch(`${API_BASE_URL}/config`, {
                      method: 'PUT',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ fairness_penalty: value })
                    })
                    if (!response.ok) throw new Error('Failed to update config')
                    await fetchState()
                  } catch (err) {
                    setError(err instanceof Error ? err.message : 'Failed to update config')
                  }
                }}
                style={{ width: '60px', marginLeft: '10px' }}
                step="0.1"
              />
            </div>
            <div style={{ marginTop: '10px' }}>
              <button onClick={resetSimulation} style={{ padding: '8px 16px', cursor: 'pointer', backgroundColor: '#FF5722', color: 'white', border: 'none', borderRadius: '4px' }}>
                Reset Simulation 🔄
              </button>
            </div>
          </section>

          <section className="grid-container" style={{ flex: 1, minWidth: '0' }}>
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
                const hasOnTripDriver = drivers.some(d => d.status === 'assigned' || d.status === 'on_trip' || d.status === 'pickup')
                const hasRider = riders.length > 0

                const paths = hoveredCell ? getPathForCell(hoveredCell.x, hoveredCell.y) : []
                let tooltipExtra = ''

                if (hasOnTripDriver) {
                  const driver = drivers[0]
                  const ride = Object.values(state.ride_requests).find(
                    r => r.assigned_driver_id === driver.id &&
                    (r.status === 'assigned' || r.status === 'pickup' || r.status === 'on_trip')
                  )
                  if (ride) {
                    if (ride.status === 'assigned' || ride.status === 'pickup') {
                      tooltipExtra = ` → Pickup at (${ride.pickup_x}, ${ride.pickup_y})`
                    } else {
                      tooltipExtra = ` → Dropoff at (${ride.dropoff_x}, ${ride.dropoff_y})`
                    }
                  }
                }

                return (
                  <div
                    key={i}
                    style={getCellStyle(x, y, hasAvailableDriver, hasOnTripDriver, hasRider)}
                    title={`(${x}, ${y})${hasAvailableDriver ? ' - Driver (available)' : ''}${hasOnTripDriver ? ' - Driver (on trip)' + tooltipExtra : ''}${hasRider ? ' - Rider' : ''}`}
                    onMouseEnter={() => setHoveredCell({ x, y })}
                    onMouseLeave={() => setHoveredCell(null)}
                  >
                  </div>
                )
              })}
            </div>
            <div style={{ marginTop: '10px', fontSize: '12px' }}>
              <div>
                <span style={{ display: 'inline-block', width: '15px', height: '10px', backgroundColor: '#4CAF50', marginRight: '5px' }}></span> Available Driver
                <span style={{ display: 'inline-block', width: '15px', height: '10px', backgroundColor: '#FFA500', marginLeft: '10px', marginRight: '5px' }}></span> Driver On Trip
                <span style={{ display: 'inline-block', width: '15px', height: '10px', backgroundColor: '#FF6B35', marginLeft: '10px', marginRight: '5px' }}></span> Driver with Rider
                <span style={{ display: 'inline-block', width: '15px', height: '10px', backgroundColor: '#F44336', marginLeft: '10px', marginRight: '5px' }}></span> Rider Waiting
              </div>
              <div style={{ marginTop: '5px' }}>
                <span style={{ display: 'inline-block', width: '15px', height: '10px', backgroundColor: '#2196F3', marginRight: '5px' }}></span> Pickup Location
                <span style={{ display: 'inline-block', width: '15px', height: '10px', backgroundColor: '#9C27B0', marginLeft: '10px', marginRight: '5px' }}></span> Dropoff Location
                <span style={{ display: 'inline-block', width: '15px', height: '10px', backgroundColor: '#FFE082', marginLeft: '10px', marginRight: '5px' }}></span> Path (on hover)
              </div>
              <div style={{ marginTop: '5px', color: '#666' }}>Hover over drivers/riders to see their paths</div>
            </div>
          </section>
        </div>

        <div style={{ minWidth: '400px', flexShrink: 0, maxHeight: 'calc(100vh - 150px)', overflowY: 'auto' }}>
          <section className="status">
            <h3>Riders ({Object.keys(state.riders).length})</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#e0e0e0' }}>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #999', color: '#000', fontWeight: 'bold' }}>ID</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #999', color: '#000', fontWeight: 'bold' }}>Position</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #999', color: '#000', fontWeight: 'bold' }}>Status</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #999', color: '#000', fontWeight: 'bold' }}>Actions</th>
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
                <tr style={{ backgroundColor: '#e0e0e0' }}>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #999', color: '#000', fontWeight: 'bold' }}>ID</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #999', color: '#000', fontWeight: 'bold' }}>Position</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #999', color: '#000', fontWeight: 'bold' }}>Status</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #999', color: '#000', fontWeight: 'bold' }}>Rides</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #999', color: '#000', fontWeight: 'bold' }}>Radius</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #999', color: '#000', fontWeight: 'bold' }}>Idle</th>
                </tr>
              </thead>
              <tbody>
                {Object.values(state.drivers).map(driver => (
                  <tr key={driver.id}>
                    <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>{driver.id}</td>
                    <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>({driver.x}, {driver.y})</td>
                    <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>
                      <span style={{
                        color: driver.status === 'available' ? 'green' : driver.status === 'assigned' || driver.status === 'on_trip' ? 'orange' : 'gray'
                      }}>
                        {driver.status}
                      </span>
                    </td>
                    <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>{driver.completed_rides}</td>
                    <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>{driver.search_radius}</td>
                    <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>{driver.idle_ticks}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <h3 style={{ marginTop: '20px' }}>Active Rides ({Object.values(state.ride_requests).filter(r => r.status !== 'completed' && r.status !== 'failed').length})</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#e0e0e0' }}>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #999', color: '#000', fontWeight: 'bold' }}>ID</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #999', color: '#000', fontWeight: 'bold' }}>Status</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #999', color: '#000', fontWeight: 'bold' }}>Pickup</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #999', color: '#000', fontWeight: 'bold' }}>Dropoff</th>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '2px solid #999', color: '#000', fontWeight: 'bold' }}>Driver</th>
                </tr>
              </thead>
              <tbody>
                {Object.values(state.ride_requests)
                  .filter(ride => ride.status !== 'completed' && ride.status !== 'failed')
                  .map(ride => (
                    <tr key={ride.id}>
                      <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>{ride.id}</td>
                      <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>
                        <span style={{
                          color: ride.status === 'waiting' ? 'orange' :
                                 ride.status === 'assigned' ? 'blue' :
                                 ride.status === 'pickup' ? 'purple' :
                                 ride.status === 'on_trip' ? 'indigo' : 'green'
                        }}>
                          {ride.status}
                        </span>
                      </td>
                      <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>({ride.pickup_x}, {ride.pickup_y})</td>
                      <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>({ride.dropoff_x}, {ride.dropoff_y})</td>
                      <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>{ride.assigned_driver_id || '-'}</td>
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
              <p>Completed Rides: {Object.values(state.ride_requests).filter(r => r.status === 'completed').length}</p>
              <p>Failed Rides: {Object.values(state.ride_requests).filter(r => r.status === 'failed').length}</p>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}

export default App
