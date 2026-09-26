# 🧳 TripMate — Human-in-the-Loop AI Trip Planning Agent

TripMate is an **AI-powered, human-in-the-loop travel planning agent** built with **LangGraph, LangChain, FastAPI, React, and LLM-based reasoning**.

Instead of simply generating a static travel plan, TripMate behaves like an interactive travel assistant that progressively builds a complete trip with the user.

The agent:

* Understands natural-language travel requests
* Extracts structured trip requirements
* Suggests transport options
* Searches real hotel options
* Generates a destination-specific itinerary
* Considers weather while planning activities
* Handles local transportation
* Plans return transportation
* Calculates the overall trip budget
* Asks for human confirmation at important decision points
* Allows the user to reject and reconsider options
* Supports editing different parts of the trip before finalization

The project was built as a practical implementation of **Agentic AI and LangGraph concepts**, with a strong focus on state management, tool usage, structured outputs, human-in-the-loop workflows, and API integration.

---

# 🎯 Project Goal

Traditional travel chatbots usually generate a complete itinerary in a single response.

That approach has a major limitation:

> The user has little control over individual decisions.

TripMate follows a different approach.

The agent breaks trip planning into multiple stages and asks the user to confirm important decisions along the way.

For example:

```text
User
 │
 ▼
Understand Trip
 │
 ▼
Transport Options
 │
 ├── Reject → Show another option
 │
 ▼
Hotel Options
 │
 ├── Reject → Show another hotel
 │
 ▼
Day-by-Day Itinerary
 │
 ├── Reject → Regenerate itinerary
 │
 ▼
Local Transportation
 │
 ▼
Return Transportation
 │
 ├── Reject → Show another option
 │
 ▼
Budget Calculation
 │
 ├── Edit → Change transport/hotel/itinerary/etc.
 │
 ▼
Final Confirmation
 │
 ▼
Trip Completed
```

This makes TripMate a **stateful agentic workflow** rather than a simple LLM chatbot.

---

# ✨ Key Features

## 1. Natural Language Trip Understanding

The user can provide a request such as:

```text
Mumbai se Manali jaana hai 5 November se 9 November tak,
2 log hain.
```

The LLM converts this into structured information:

```text
Origin: Mumbai
Destination: Manali
Start Date: 2026-11-05
End Date: 2026-11-09
Travelers: 2
Budget: moderate
```

The structured representation is validated using **Pydantic models**.

---

## 2. Structured Trip State

TripMate maintains a shared state throughout the entire workflow.

The state stores information such as:

* User request
* Parsed trip intent
* Transport options
* Selected transport
* Hotel options
* Selected hotel
* Itinerary
* Scooter selection
* Return transport
* Budget
* User decisions
* Retry/edit information

This state is passed between LangGraph nodes.

---

# 🧠 Agent Architecture

TripMate uses **LangGraph** to represent the travel planning process as a graph of nodes and transitions.

### Main nodes

```text
START
  │
  ▼
parse_intent
  │
  ▼
find_transport
  │
  ▼
find_hotel
  │
  ▼
generate_itinerary
  │
  ▼
approve_itinerary
  │
  ▼
plan_local_travel
  │
  ▼
find_return_transport
  │
  ▼
compute_budget
  │
  ▼
END
```

Conditional transitions allow the graph to move backwards when the user rejects an option.

For example:

```text
find_transport
      │
      ├── Accept ─────────► find_hotel
      │
      └── Reject ─────────► find_transport
```

Similarly:

```text
generate_itinerary
        │
        ▼
approve_itinerary
        │
        ├── Accept ───────► plan_local_travel
        │
        └── Reject ───────► generate_itinerary
```

This is one of the main reasons LangGraph is used instead of implementing the entire workflow as a normal sequential Python script.

---

# 🤝 Human-in-the-Loop

Human approval is a core part of TripMate.

The agent does not automatically finalize important decisions.

For example:

```text
The cheapest option is [SIMULATED] ...
Shall I go ahead with this?
```

The user can:

```text
yes
```

or select another option.

The same concept is used for:

* Transport
* Hotels
* Itinerary
* Local transportation
* Return journey
* Final booking confirmation

LangGraph's interrupt/resume workflow is used to pause execution and continue it later with the user's response.

---

# 🔄 Example Agent Interaction

### User

```text
Mumbai se Manali jaana hai 5 November se 9 November tak,
2 log hain.
```

### Agent

```text
The cheapest option is [SIMULATED] ...
Shall I go ahead with this?
```

### User

```text
LTT–Chandigarh + Road
```

### Agent

```text
I found Durga in Manali for USD 8.57/night...
Shall I book this?
```

### User

```text
Snow Apple Resort
```

### Agent

```text
Here's a draft itinerary:

2026-11-05:
Arrive in Manali...
Visit Hadimba Temple...

2026-11-06:
Explore Solang Valley...

...
Does this work for you?
```

The user can then accept or request a new itinerary.

---

# 🏨 Real Hotel Search

TripMate integrates **StayingAPI** for hotel search.

The application sends information such as:

```text
Destination
Check-in
Check-out
Number of adults
Budget level
```

The API can return asynchronous search jobs, which TripMate handles by polling the job status before processing the results.

Hotel information includes:

* Property name
* Location
* Price per night
* Total price
* Currency
* Number of nights
* Guest rating

Example:

```text
Durga
USD 8.57/night
Total: USD 34.26
Rating: 10.0
```

---

# 🚆 Transport Planning

Transport is currently **simulated**.

The transport planner uses the LLM to generate realistic-looking route options based on:

* Origin
* Destination
* Date
* Geography
* Railway/airport connectivity

Every generated option is explicitly marked:

```text
[SIMULATED]
```

This is intentional.

TripMate does **not** claim that these simulated options represent real-time availability or real booking inventory.

Example:

```text
[SIMULATED] CST–Pathankot + Road
[SIMULATED] LTT–Chandigarh + Road
[SIMULATED] Mumbai–Bhuntar (Air India)
```

A real transport/booking API can be integrated later.

---

# 🌦️ Weather-Aware Itinerary

TripMate retrieves weather information for the destination and trip dates.

Weather information can include:

```text
Date
Condition
Minimum temperature
Maximum temperature
Rain probability/likelihood
```

The weather information is passed to the itinerary-generation LLM.

This allows the agent to adapt activities according to conditions.

For example:

```text
Rain expected
      ↓
Prefer indoor/local activities

Clear weather
      ↓
Prefer outdoor sightseeing
```

---

# 🗺️ Destination-Specific Itinerary

The itinerary generator uses:

* Destination
* Region
* Trip dates
* Number of travelers
* Budget level
* Weather

The LLM is instructed to:

* Keep activities destination-specific
* Avoid attractions from other cities
* Avoid inventing fake attractions
* Consider weather
* Avoid repeating activities
* Keep daily plans practical
* Generate 2–3 activities per day

Example Manali itinerary activities:

```text
Hadimba Temple
Van Vihar
Solang Valley
Tibetan Monastery
Manu Temple
Vashisht
Naggar
Beas River
```

The previous external places-data dependency was intentionally removed from the itinerary-generation pipeline because incorrect geographic data could result in attractions from another city being suggested.

---

# 🛵 Local Transportation

TripMate can suggest a scooter rental for local transportation.

The user can:

```text
Accept
```

or

```text
Reject
```

the proposed rental.

The selected scooter is then included in the final budget calculation.

---

# 🔁 Return Journey

After completing the itinerary and local transportation step, TripMate searches for simulated return transportation.

The route is reversed:

```text
Outbound:

Mumbai → Manali

Return:

Manali → Mumbai
```

The user can select, reject, or reconsider the return option.

---

# 💰 Automatic Budget Calculation

After the major trip decisions are made, TripMate calculates the estimated trip budget.

Current budget components include:

```text
Outbound transport
Hotel
Scooter
Return transport
```

The final budget is represented using a structured Pydantic model.

Example:

```text
Transport: ₹2500
Stay: ₹...
Scooter: ₹...
Return: ₹...

Total: ₹...
```

Hotel currencies are converted to INR before being included in the total.

---

# ✏️ Trip Editing

TripMate supports changing decisions even near the end of the workflow.

If the user does not want to finalize the trip, the agent asks:

```text
What would you like to change?

Transport
Hotel
Itinerary
Scooter
Return journey

Or say 'cancel' to stop planning.
```

The user's response is classified into an edit target.

For example:

```text
"hotel"
       ↓
find_hotel

"change the itinerary"
       ↓
generate_itinerary

"train"
       ↓
find_transport

"return journey"
       ↓
find_return_transport
```

This demonstrates stateful graph routing instead of restarting the entire application.

---

# 🏗️ Project Structure

```text
tripmate-agent/
│
├── app/
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   ├── state.py
│   │   ├── llm.py
│   │   └── utils.py
│   │
│   ├── tools/
│   │   ├── weather_tool.py
│   │   ├── places_tool.py
│   │   ├── transport_tool.py
│   │   ├── hotel_tool.py
│   │   ├── scooter_tool.py
│   │   └── currency_tool.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   │
│   ├── __init__.py
│   └── main.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── ChatWindow.jsx
│   │   │   └── InputBar.jsx
│   │   │
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   │
│   ├── vite.config.js
│   ├── package.json
│   └── ...
│
├── tests/
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

# 📂 Backend Structure

## `app/agent/`

Contains the actual agent logic.

### `graph.py`

Defines the LangGraph workflow.

Responsible for:

* Creating the graph
* Registering nodes
* Defining edges
* Conditional routing
* Checkpointing
* Managing graph state

---

### `nodes.py`

Contains the main agent nodes:

```text
parse_intent()
find_transport()
find_hotel()
generate_itinerary()
approve_itinerary()
plan_local_travel()
find_return_transport()
compute_budget()
```

Each node performs one major part of the trip-planning workflow.

---

### `state.py`

Defines the shared `TripState`.

The state allows information generated by one node to be used by later nodes.

---

### `llm.py`

Contains the LLM configuration.

The current project uses a Groq-hosted model.

---

### `utils.py`

Contains helper logic for interpreting user decisions.

Examples:

```text
User choice
Confirmation
Edit target
```

---

# 🧰 Tools

The `app/tools/` directory contains integrations and helper tools used by the agent.

### `weather_tool.py`

Retrieves weather information.

### `hotel_tool.py`

Integrates with StayingAPI and processes hotel search results.

### `transport_tool.py`

Generates clearly marked simulated transport options.

### `scooter_tool.py`

Provides local scooter rental estimates.

### `currency_tool.py`

Converts hotel costs into INR for budget calculation.

### `places_tool.py`

Contains OpenTripMap integration experiments.

It is currently **not used by the itinerary-generation pipeline** because destination-specific itinerary generation is handled directly by the LLM with weather/context constraints.

---

# 📦 Data Models

`app/models/schemas.py` contains Pydantic models used throughout the system.

Important models include:

```text
TripIntent
TransportOption
HotelOption
BudgetItem
TripBudget
WeatherDay
Place
DayPlan
ScooterOption
StartTripRequest
ResumeTripRequest
TripResponse
```

Using structured models prevents different components of the application from passing arbitrary data formats around.

---

# 🌐 FastAPI Backend

The backend exposes the agent through REST APIs.

## Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

---

## Start Trip

```http
POST /trip/start
```

Request:

```json
{
  "message": "Mumbai se Manali jaana hai 5 November se 9 November tak, 2 log hain.",
  "thread_id": "trip-001"
}
```

---

## Resume Trip

```http
POST /trip/resume
```

Request:

```json
{
  "message": "haan",
  "thread_id": "trip-001"
}
```

The same `thread_id` allows the agent to resume the paused workflow.

FastAPI automatically exposes interactive API documentation through Swagger UI at `/docs`, with the OpenAPI schema available through the application as well.

---

# 🎨 Frontend

The frontend is built using:

* React
* Vite
* JavaScript
* CSS

The interface provides:

* Chat-based interaction
* Transport cards
* Hotel cards
* Selection buttons
* Agent messages
* User messages
* Trip completion summary
* Budget display

Vite provides the development server and production build tooling for the frontend.

---

# 🔐 Environment Variables

Create a `.env` file in the project root.

Example:

```env
GROQ_API_KEY=your_groq_api_key

STAYINGAPI_KEY=your_stayingapi_key

OPENWEATHER_API_KEY=your_openweather_api_key

OPENTRIPMAP_KEY=your_opentripmap_api_key
```

**Never commit `.env` to GitHub.**

The project uses:

```text
.env
```

for actual secrets and:

```text
.env.example
```

for documenting required environment variables.

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>

cd tripmate-agent
```

---

## 2. Create Python virtual environment

Python 3.13 is currently used for the backend.

```bash
py -3.13 -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

---

## 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure environment variables

Create:

```text
.env
```

and add the required API keys.

---

# 🚀 Running the Backend

From the project root:

```powershell
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

# 🚀 Running the Frontend

Open another terminal:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Start the development server:

```powershell
npm run dev
```

The Vite development server will normally run on:

```text
http://localhost:5173
```

---

# 🔌 Frontend → Backend Flow

The frontend communicates with the FastAPI backend.

```text
React UI
   │
   │ POST /trip/start
   ▼
FastAPI
   │
   ▼
LangGraph
   │
   ├── LLM
   ├── Hotel API
   ├── Weather API
   └── Other tools
   │
   ▼
Agent response
   │
   ▼
FastAPI
   │
   ▼
React UI
```

When the graph reaches a human approval point, the backend returns a response indicating that the agent is waiting for user input.

The frontend sends the user's response to:

```text
POST /trip/resume
```

The graph then continues from its saved state.

---

# 🧠 Technologies Used

| Technology  | Purpose                                                 |
| ----------- | ------------------------------------------------------- |
| Python      | Backend and agent implementation                        |
| LangChain   | LLM integration and structured interactions             |
| LangGraph   | Stateful agent workflow and human-in-the-loop execution |
| Groq        | LLM inference                                           |
| Pydantic    | Structured data validation                              |
| FastAPI     | REST API backend                                        |
| React       | Frontend UI                                             |
| Vite        | Frontend development/build tooling                      |
| StayingAPI  | Real hotel search                                       |
| OpenWeather | Weather information                                     |
| OpenTripMap | Places API experimentation                              |
| Requests    | External API communication                              |
| Uvicorn     | ASGI server                                             |

---

# 🧩 Agentic AI Concepts Demonstrated

This project was designed around practical Agentic AI concepts rather than only building an LLM chatbot.

## 1. Structured Output

Natural-language user input is converted into structured Pydantic models.

```text
Natural Language
      ↓
LLM
      ↓
TripIntent
```

---

## 2. Tool Usage

The agent interacts with external services through dedicated tools.

```text
Agent
 ├── Weather Tool
 ├── Hotel Tool
 ├── Currency Tool
 └── Scooter Tool
```

---

## 3. State Management

The complete trip is maintained in a shared `TripState`.

This allows later nodes to access earlier decisions.

---

## 4. Conditional Routing

The graph dynamically decides what node should execute next.

```text
User rejects hotel
       ↓
find_hotel
       ↓
new hotel options
```

---

## 5. Human-in-the-Loop

The agent pauses at important decisions and waits for human input before continuing.

---

## 6. Checkpointing

Trip state is associated with a thread ID so the workflow can be resumed after an interruption.

---

## 7. Separation of Concerns

The project separates:

```text
Agent Logic
     ↓
Tools
     ↓
Data Models
     ↓
API Layer
     ↓
Frontend
```

This makes the system easier to maintain and extend.

---

# 🧪 Current Limitations

TripMate is currently a **functional prototype / portfolio project**, not a production booking platform.

### Transport

Transport options are currently simulated:

```text
[SIMULATED]
```

They are not real-time availability or booking results.

### Hotel

Hotel search uses a real API, but final booking is currently represented as part of the agent workflow rather than completing a real financial transaction.

### Weather

Weather availability depends on the capabilities and forecast window of the configured weather API.

### Booking

The current system simulates final booking confirmation.

No real payment or ticket purchase is performed.

### Local transportation

Scooter pricing is currently represented through the project's scooter tool rather than a real-time rental marketplace.

---

# 🔮 Future Improvements

Possible future versions can add:

## Real Transport APIs

Replace simulated transport with real:

```text
Train APIs
Flight APIs
Bus APIs
```

---

## Real Booking

Integrate:

```text
Hotel booking
Transport booking
Payment
Booking confirmation
```

---

## Google Calendar Integration

After final confirmation:

```text
Trip
 ↓
Calendar events
 ↓
Travel dates
Hotel stay
Activities
Return journey
```

A Google Calendar invitation can be generated for the finalized itinerary.

---

## Better Memory

Introduce persistent storage for:

* User preferences
* Previous trips
* Favorite hotels
* Budget preferences
* Travel style

---

## Authentication

Add user accounts and secure trip histories.

---

## Production Database

Possible stack:

```text
PostgreSQL
Redis
```

for persistent state, caching, and user data.

---

## Deployment

Potential deployment architecture:

```text
React/Vite
      ↓
Frontend Hosting

FastAPI
      ↓
Cloud Server

LangGraph
      ↓
LLM + External APIs

Database
      ↓
PostgreSQL
```

---

# 📊 Current End-to-End Workflow

The complete TripMate workflow is:

```text
                    ┌─────────────────┐
                    │      USER       │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Parse Intent   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Transport    │
                    └────────┬────────┘
                             │
                     Human Approval
                             │
                             ▼
                    ┌─────────────────┐
                    │      Hotel      │
                    └────────┬────────┘
                             │
                     Human Approval
                             │
                             ▼
                    ┌─────────────────┐
                    │   Itinerary     │
                    │ + Weather       │
                    └────────┬────────┘
                             │
                     Human Approval
                             │
                             ▼
                    ┌─────────────────┐
                    │ Local Transport │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Return Transport│
                    └────────┬────────┘
                             │
                     Human Approval
                             │
                             ▼
                    ┌─────────────────┐
                    │  Budget Rollup  │
                    └────────┬────────┘
                             │
                       Final Approval
                             │
                             ▼
                    ┌─────────────────┐
                    │   TRIP READY    │
                    └─────────────────┘
```

---

# 📸 Example

Example request:

```text
Mumbai se Manali jaana hai
5 November se 9 November tak
2 log hain.
```

TripMate progressively produces:

```text
✓ Transport options

✓ Hotel options

✓ Weather-aware itinerary

✓ Local transportation option

✓ Return transport

✓ Complete budget

✓ Final confirmation
```

Instead of producing everything in one LLM response, the system **reasons through the trip as a multi-step stateful workflow**.

---

# 🎓 Learning Outcomes

Building TripMate provided practical experience with:

* LLM application development
* Prompt engineering
* Structured LLM outputs
* Pydantic
* LangChain
* LangGraph
* Stateful agents
* Human-in-the-loop workflows
* Graph-based agent orchestration
* Tool calling/integrations
* REST APIs
* FastAPI
* React
* Vite
* External API integration
* Error handling
* API polling
* Environment management
* Git/GitHub
* Full-stack AI application architecture

---

# 🛠️ Development Philosophy

TripMate was developed incrementally rather than attempting to build the entire agent at once.

The development progression was approximately:

```text
LLM
 ↓
Structured Intent
 ↓
Tools
 ↓
LangGraph
 ↓
State
 ↓
Human-in-the-Loop
 ↓
External APIs
 ↓
FastAPI
 ↓
React Frontend
 ↓
Complete Agent Workflow
```

This approach made it possible to understand each Agentic AI concept while integrating it into a realistic application.

---

# 📌 Project Status

### Current Status: Functional Prototype ✅

Implemented:

* [x] Natural-language trip input
* [x] Structured trip intent
* [x] LangGraph workflow
* [x] Stateful agent execution
* [x] Human-in-the-loop
* [x] Simulated transport planning
* [x] Real hotel search
* [x] Weather integration
* [x] Destination-specific itinerary generation
* [x] Local scooter planning
* [x] Return transport planning
* [x] Budget calculation
* [x] Trip editing flow
* [x] FastAPI backend
* [x] React frontend
* [x] Vite development setup
* [x] Git/GitHub project structure

Planned:

* [ ] Real transport APIs
* [ ] Real booking APIs
* [ ] Google Calendar integration
* [ ] Authentication
* [ ] Persistent database
* [ ] Production deployment
* [ ] User preference memory

---

# 👨‍💻 Author

**Aakarshan Parimoo**

B.Tech — Computer Science & Engineering
IIIT Una

Interests:

* Artificial Intelligence
* Machine Learning
* Deep Learning
* NLP
* Agentic AI
* LangChain
* LangGraph
* Full-Stack AI Applications

---

# ⭐ If You Found This Project Interesting

Feel free to explore the code, experiment with the agent workflow, and extend TripMate with real booking and travel APIs.
