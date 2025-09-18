# 🛺 Ride Dispatch System

A simplified ride-hailing backend system with FastAPI and React frontend, built for technical assessment. The system operates in a grid-based city where riders request rides and drivers are dispatched based on ETA, fairness, and availability.

## 🎯 Overview

This system simulates a ride-hailing platform with:
- **FastAPI backend** managing drivers, riders, and ride requests
- **Dispatch algorithm** balancing low ETA with driver fairness
- **Fallback mechanism** when drivers reject rides
- **React frontend** for visualization and simulation control
- **Grid-based world** with manual time advancement

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Git

### Setup & Run

**1. Clone and Setup Backend:**
```bash
git clone <your-repo-url>
cd ride-dispatch-sim

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**2. Setup Frontend (in new terminal):**
```bash
cd frontend
npm install
npm start
```

**3. Access the Application:**
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Frontend UI: http://localhost:3000

## 🧩 System Architecture

### Entities

**Driver:**
- Unique ID, current location (x, y)
- Status: `available`, `on_trip`, or `offline`
- Search radius (grows with idle time)
- Completed rides counter

**Rider:**
- Unique ID, pickup/dropoff locations (x, y)
- Status: `waiting`, `picked_up`, `completed`

**RideRequest:**
- Rider ID, pickup/dropoff coordinates
- Status: `waiting`, `assigned`, `completed`, `failed`
- Assigned driver, rejection tracking

### Flow

1. **Ride Request:** Rider requests ride via API/frontend
2. **Dispatch:** System finds best available driver using algorithm
3. **Assignment:** Driver accepts/rejects based on distance/workload
4. **Fallback:** If rejected, try next-best driver
5. **Movement:** Driver moves toward pickup → dropoff (1 unit per tick)
6. **Completion:** Ride marked completed when dropoff reached

## 🧠 Dispatch Algorithm

Our algorithm balances **fairness**, **efficiency**, and **low ETA**:

### Priority Logic
1. **Find eligible drivers** within search radius of pickup
2. **Sort by fairness** - drivers with fewer completed rides first
3. **Secondary sort by distance** - closest drivers preferred
4. **Assign to top priority** available driver

### Driver Acceptance
- Drivers accept rides if pickup is within their search radius
- Search radius starts at 5 units, grows +1 every 10 idle ticks
- Maximum search radius: 20 units
- Uses Manhattan distance: `|x1-x2| + |y1-y2|`

### Fallback Mechanism
- If driver rejects, immediately try next-best driver
- Track rejected drivers to avoid reassignment
- Apply 5-tick cooldown if no drivers available
- Mark ride as failed after 3 retry cycles

## 🗺 Grid World

- **100x100 grid** coordinate system (0-99 on both axes)
- **Manhattan distance** for all calculations
- **Manual time advancement** via `/tick` endpoint
- **Deterministic simulation** - same inputs = same results
- **In-memory state** - no database required

## 📡 API Endpoints

### Core Operations
- `POST /drivers` - Create driver at (x,y) position
- `POST /riders` - Create rider at (x,y) position  
- `POST /rides` - Request ride with pickup/dropoff
- `GET /state` - Get complete simulation state
- `POST /tick` - Advance time by one tick

### Configuration
- `PUT /config` - Update fairness penalty weight

### Example Usage
```bash
# Add a driver at position (10, 15)
curl -X POST "http://localhost:8000/drivers" -H "Content-Type: application/json" -d '{"x": 10, "y": 15}'

# Request a ride
curl -X POST "http://localhost:8000/rides" -H "Content-Type: application/json" -d '{"rider_id": "rider_1", "pickup_x": 20, "pickup_y": 25, "dropoff_x": 50, "dropoff_y": 75}'

# Advance simulation
curl -X POST "http://localhost:8000/tick"
```

## 💻 Frontend Features

**Simple Grid Visualization:**
- 10x10 grid showing driver/rider positions
- Green "D" for available drivers
- Red "R" for waiting riders
- Yellow "DR" for drivers on trips

**Control Panel:**
- Add Driver/Rider buttons
- Request Ride functionality
- Next Tick advancement
- Fairness penalty adjustment

**Status Tables:**
- Real-time driver status and positions
- Active ride requests and assignments
- Automatic state polling every 2 seconds

## ⚙️ Configuration

**Default Settings:**
- Initial search radius: 5 units
- Maximum search radius: 20 units
- Radius growth: +1 every 10 idle ticks
- Rejection cooldown: 5 ticks
- Fairness penalty weight: 1.0

**Adjustable Parameters:**
- Fairness penalty weight (via UI or API)
- Driver acceptance criteria
- Movement patterns

## 🧪 Key Design Decisions

### Assumptions Made
1. **Driver Acceptance:** Simplified to distance-based (no complex behavioral modeling)
2. **Movement:** One grid unit per tick in cardinal directions only
3. **Grid Size:** 100x100 for demo, easily configurable
4. **State Management:** In-memory dictionaries for simplicity
5. **UI Scope:** Basic functionality over polish for time constraints

### Fairness Implementation
- **Primary fairness:** Drivers with fewer completed rides get priority
- **Secondary efficiency:** Among equal drivers, closest gets priority
- **Configurable weight:** Adjustable fairness penalty for fine-tuning

### Scalability Considerations
- Modular code structure for easy extension
- Clean separation between models, algorithms, and API
- Simple state management that could easily move to database
- Algorithm complexity: O(n log n) for driver sorting

## 🔍 Testing & Validation

**Manual Testing Scenarios:**
1. Create multiple drivers and riders
2. Request rides and observe dispatch decisions
3. Test rejection fallback with distant drivers
4. Verify fairness by checking ride distribution
5. Test edge cases (no available drivers, grid boundaries)

**Key Validation Points:**
- Rides assigned to closest available driver
- Fair distribution among drivers over time
- Proper fallback when rejections occur
- Correct movement toward pickup/dropoff
- Grid boundary constraints respected

## 📁 Project Structure

```
ride-dispatch-sim/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── main.py              # FastAPI app with all endpoints
│   └── venv/                # Python virtual environment
└── frontend/
    ├── src/
    │   ├── App.tsx           # Main React component
    │   └── index.tsx         # React entry point
    ├── package.json
    └── public/
```

## 🎓 Learning Outcomes

This implementation demonstrates:
- **Algorithm Design:** Balancing multiple objectives (fairness, efficiency, ETA)
- **System Architecture:** Clean separation of concerns
- **API Design:** RESTful endpoints with proper state management
- **Real-time Systems:** Simulation with discrete time advancement
- **Full-stack Development:** Backend + Frontend integration

## 🔧 Future Enhancements

**Potential Extensions:**
- Persistent database storage
- Real-time WebSocket updates
- Advanced driver behavioral models
- Route optimization algorithms
- Performance metrics and analytics
- Multi-rider ride sharing
- Dynamic pricing algorithms

---

**Built for Technical Assessment** | **Time Constraint: ~45 minutes coding** | **Focus: Working system over perfection**
