# 🛺 Ride Dispatch System - Product Requirements Document (PRD)

**Version**: 1.1
**Status**: Final
**Author**: Jack (PM)

## 1. Goals and Background Context

### Goals
- Correctly implement the full ride lifecycle: `waiting` → `assigned` → `pickup` → `on_trip` → `completed` / `failed`.
- Develop a dispatch algorithm that balances low ETA with fairness for drivers.
- Implement realistic driver behavior where acceptance is based on logical criteria (distance, workload).
- Maximize system efficiency by fulfilling as many rides as possible.
- Ensure a fast and effective fallback mechanism if the primary driver for a ride rejects the request.
- Build a simple, transparent UI to visualize the grid state and allow for manual simulation control.

### Background Context
This project is a one-hour technical assessment to build a simplified ride-hailing backend simulator using FastAPI and a basic React frontend. The system operates in a deterministic, grid-based world where time advances in discrete, user-triggered "ticks." The core challenge is designing and implementing the dispatch and driver acceptance logic.

### Change Log
| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| Sep 18, 2025 | 1.1 | Finalized 4-story plan and detailed algorithm requirements. | Jack (PM) |
| Sep 18, 2025 | 1.0 | Initial PRD draft for interview project. | Jack (PM) |

---

## 2. Requirements

### Functional Requirements (FR)
1.  **FR1: Grid World:** The system shall operate on a 100x100 2D grid.
2.  **FR2: Entities:** The system must support `Driver`, `Rider`, and `RideRequest` entities with their specified attributes.
3.  **FR3: Ride Request:** A `Rider` must be able to request a ride from a pickup to a dropoff location.
4.  **FR4: Dispatch Logic:** The system shall automatically assign the best available `Driver` to a `RideRequest`.
5.  **FR5: Driver Acceptance Logic:** An assigned `Driver` shall automatically accept or reject a ride based on distance and workload.
6.  **FR6: Rejection Fallback:** If a `Driver` rejects a ride, the system must immediately attempt to find the next-best driver.
7.  **FR7: Movement:** `Drivers` shall move one grid unit per tick.
8.  **FR8: Ride Lifecycle:** A `RideRequest` must transition through all statuses from `waiting` to `completed` or `failed`.
9.  **FR9: API Endpoints:** The backend must provide API endpoints to manage entities, control the simulation, and update configuration.
10. **FR10: Frontend Visualization:** The frontend shall visualize the grid, entity locations, and ride statuses.

### Non-Functional Requirements (NFR)
1.  **NFR1: Determinism:** The simulation must be deterministic.
2.  **NFR2: In-Memory State:** The system shall not require a persistent database; all state will be managed in-memory.
3.  **NFR3: Extensibility:** The code shall be clean, modular, and designed for future extensibility.
4.  **NFR4: Rigorous Code Documentation:** All functions, classes, and complex logic must include clear inline documentation (docstrings/comments).
5.  **NFR5: Simplicity:** The implementation should favor simplicity and clarity, using the most straightforward methods that meet requirements.

---

## 3. User Interface Design Goals
-   **Overall UX Vision**: A simple, transparent window into the simulation state, allowing easy setup of scenarios and observation of the results.
-   **Core Screens and Views**: A single-page interface containing a Controls Panel, a Grid Canvas, and a State Panel (Table).
-   **Accessibility & Branding**: Out of scope for this one-hour assessment.
-   **Target Device and Platforms**: Web application for laptops, built with React.

---

## 4. Technical Assumptions
-   **Repository Structure**: **Monorepo** (a single repository with `frontend/` and `backend/` folders).
-   **State Management**: The backend will use in-memory **Python dictionaries** for simulation state. The frontend can use browser **Local Storage** for UI state.
-   **Service Architecture**: **Monolith** (a single, self-contained FastAPI service).
-   **Testing Requirements**: **Unit Tests Only** for core backend logic.

---

## 5. Epic 1: Ride Dispatch Simulator MVP
**Epic Goal**: Build, test, and run a complete, in-memory ride dispatch simulator with a functional backend API and a minimal frontend for visualization and control.

### Story 1.1: Project Scaffolding
*As a developer, I want a simple monorepo containing an initialized FastAPI backend and a React frontend, so I have a clean, runnable structure in under 10 minutes.*
* **Acceptance Criteria**:
    1.  A single Git repository is created with `backend/` and `frontend/` subdirectories.
    2.  The `backend/` folder contains a basic, runnable FastAPI application within a **Python 3.12+ virtual environment**.
    3.  The `frontend/` folder contains a basic, runnable React application (using Vite) within a **Node.js 20+ environment**.
    4.  A root-level `README.md` file is created.
    5.  All code must have **rigorous inline documentation**.

### Story 1.2: Backend Logic, Models, & State
*As a developer, I want to define the core data models, manage the simulation state in-memory, and implement the primary dispatch algorithms, so the brain of the backend is complete.*
* **Acceptance Criteria**:
    1.  Pydantic models for `Driver`, `Rider`, and `RideRequest` are defined.
    2.  A state module holds all simulation data in Python dictionaries.
    3.  The dispatch algorithm finds drivers within a circular **search radius** and prioritizes them in a queue based on the **lowest number of completed rides**.
    4.  The driver acceptance logic rejects rides if the pickup location is outside their current search radius.
    5.  A driver's search radius **increases over time** while they are idle.
    6.  All distance calculations use **Manhattan distance**.
    7.  `available` drivers move **randomly** one grid unit per tick.

### Story 1.3: Backend API & Ride Lifecycle
*As a developer, I want to expose all necessary API endpoints and implement the complete ride lifecycle logic, so the backend is fully interactive and robust.*
* **Acceptance Criteria**:
    1.  `POST` endpoints for `/drivers`, `/riders`, `/rides`, and `GET /state` are implemented.
    2.  A `PUT /config` endpoint allows updating the **fairness penalty** weight.
    3.  The `POST /tick` endpoint is implemented, triggering movement for all drivers.
    4.  The full ride lifecycle is implemented: handling rejections with a cooldown, attempting **fallbacks**, and marking rides `completed` or `failed`.

### Story 1.4: Complete Frontend Visualization & Controls
*As a user, I want a single-page interface to visualize the grid, see the system state, and control the simulation, so I can run and observe different scenarios.*
* **Acceptance Criteria**:
    1.  The frontend is a single page that polls `GET /state`.
    2.  A visual grid displays entities with color and label codes: Green "D" (Available Driver), Red "R" (Waiting Rider), Yellow "DR" (Driver On-Trip).
    3.  When hovering over a "DR" dot, a line is drawn to the dropoff location.
    4.  A control panel with functional buttons for "Add Driver," "Add Rider," "Request Ride," and "Next Tick" is present.
    5.  A data table displays the current status of all drivers and ride requests.
    6.  An input field or slider on the UI allows the user to **adjust the fairness penalty**.