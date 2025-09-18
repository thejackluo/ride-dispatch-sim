import './App.css'

/**
 * Main Application Component
 * Provides the primary UI for the Ride Dispatch Simulator
 * Currently displays a placeholder for the grid visualization
 */
function App() {
  return (
    <div className="App">
      <header>
        <h1>🛺 Ride Dispatch Simulator</h1>
      </header>

      <main>
        <section className="controls">
          <h2>Controls</h2>
          <div className="control-buttons">
            <button>Add Driver</button>
            <button>Add Rider</button>
            <button>Request Ride</button>
            <button>Next Tick</button>
          </div>
        </section>

        <section className="grid-container">
          <h2>City Grid</h2>
          <div className="grid-placeholder" style={{
            width: '500px',
            height: '500px',
            border: '2px solid #ccc',
            backgroundColor: '#f5f5f5',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <p>Grid visualization placeholder (100x100)</p>
          </div>
        </section>

        <section className="status">
          <h2>System Status</h2>
          <p>Ready to connect to backend API</p>
        </section>
      </main>
    </div>
  )
}

export default App
