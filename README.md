# Mini CRM - Lead Distribution System

A FastAPI service for automatically distributing leads among operators based on source channels with weighted distribution and load balancing.

## Overview

This system manages the distribution of incoming leads (customer requests) from various sources (bots/channels) to available operators. The distribution algorithm considers operator weights per source and their current workload to ensure fair and efficient allocation.

## Technology Stack

- **Language**: Python 3.11+
- **Web Framework**: FastAPI
- **ORM**: SQLAlchemy (sync)
- **Database**: SQLite
- **Containerization**: Docker & Docker Compose

## Data Model

### Core Entities

1. **Operator**
   - Represents a customer service operator
   - Has an active/inactive status
   - Has a maximum load limit (number of active requests they can handle)
   - Can be assigned different weights for different sources

2. **Lead**
   - Represents an end customer/client
   - Uniquely identified by `external_id`
   - Can have multiple requests from different sources
   - Additional fields: name, email, phone

3. **Source**
   - Represents a channel/bot from which requests arrive
   - Has a unique name
   - Can have multiple operators configured with different weights

4. **OperatorSourceWeight**
   - Configuration table linking operators to sources
   - Defines the weight (competency/traffic share) for each operator per source
   - Used by the distribution algorithm

5. **Request**
   - Represents a specific contact/inquiry from a lead via a source
   - Linked to a lead, source, and optionally an operator
   - Has a status (active/closed) which affects operator load calculation

### Database Schema Relationships

```
Operator (1) ──< (N) OperatorSourceWeight (N) >── (1) Source
    │                                                  │
    │                                                  │
    └──< (N) Request (N) >── (1) Lead                 │
             └────────────────────< (1) ──────────────┘
```

## Distribution Algorithm

### How Lead Distribution Works

When a new request is created, the system follows these steps:

#### 1. Identify or Create Lead
- Search for an existing lead by `external_id`
- If not found, create a new lead with provided information
- This ensures the same customer is recognized across different sources

#### 2. Find Available Operators
The system queries for operators that meet ALL these criteria:
- **Configured for the source**: Have a weight entry in `OperatorSourceWeight`
- **Active**: `is_active = True`
- **Below capacity**: Current load < `max_load`

**Load Calculation**:
- Load = number of requests with `status = "active"` assigned to the operator
- When a request status changes to "closed", it no longer counts toward load
- This allows operators to receive new requests as they complete existing ones

#### 3. Weighted Random Selection
Among available operators, selection uses weighted probability:

```
Probability(operator) = operator_weight / sum_of_all_weights
```

**Example**:
- Operator A has weight 10
- Operator B has weight 30
- Operator C has weight 60
- Total weights = 100

Distribution probabilities:
- Operator A: 10% of requests
- Operator B: 30% of requests
- Operator C: 60% of requests

**Implementation**: Uses Python's `random.choices()` with weights parameter for statistically fair distribution over time.

#### 4. Handle No Available Operators
If no operators meet the criteria (all inactive, at capacity, or none configured):
- Request is created WITHOUT operator assignment (`operator_id = NULL`)
- Returns HTTP 201 with `operator_id: null` in response
- This allows tracking of unassigned requests for later manual assignment or capacity planning

## API Endpoints

### Operator Management

#### Create Operator
```http
POST /operators
Content-Type: application/json

{
  "name": "John Doe",
  "is_active": true,
  "max_load": 10
}
```

#### List All Operators
```http
GET /operators
```

#### Get Operator Details
```http
GET /operators/{operator_id}
```

#### Update Operator
```http
PATCH /operators/{operator_id}
Content-Type: application/json

{
  "is_active": false,
  "max_load": 15
}
```

### Source Management

#### Create Source
```http
POST /sources
Content-Type: application/json

{
  "name": "Telegram Bot",
  "description": "Main Telegram channel"
}
```

#### List All Sources
```http
GET /sources
```

#### Configure Source Weights
```http
POST /sources/{source_id}/weights
Content-Type: application/json

[
  {"operator_id": 1, "weight": 10},
  {"operator_id": 2, "weight": 30},
  {"operator_id": 3, "weight": 60}
]
```

This endpoint replaces all existing weight configurations for the source.

#### Get Source Weight Configuration
```http
GET /sources/{source_id}/weights
```

### Request Management

#### Register New Request (Main Endpoint)
```http
POST /requests
Content-Type: application/json

{
  "lead_external_id": "customer_12345",
  "source_id": 1,
  "message": "I have a question about pricing",
  "lead_name": "Jane Smith",
  "lead_email": "jane@example.com",
  "lead_phone": "+1234567890"
}
```

**Response**:
```json
{
  "id": 1,
  "lead_id": 1,
  "source_id": 1,
  "operator_id": 2,
  "operator_name": "John Doe",
  "status": "active",
  "message": "I have a question about pricing",
  "created_at": "2025-01-27T10:30:00"
}
```

#### List Requests
```http
GET /requests
GET /requests?source_id=1
GET /requests?operator_id=2
```

#### Update Request Status
```http
PATCH /requests/{request_id}/status?status=closed
```

Changing status to "closed" reduces the operator's current load.

### Analytics & Viewing

#### List All Leads with Their Requests
```http
GET /requests/leads/all
```

Shows that one lead can have multiple requests from different sources.

#### Get Distribution Statistics
```http
GET /requests/distribution/stats
```

Shows how requests are distributed across operators for each source.

## Installation & Running

### Method 1: Local Development

#### Prerequisites
- Python 3.11 or higher
- pip

#### Steps
```bash
# Clone the repository
cd miniCRM

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

#### Access API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Method 2: Docker

#### Prerequisites
- Docker
- Docker Compose

#### Steps
```bash
cd miniCRM

# Build and run
docker-compose up --build

# Run in background
docker-compose up -d
```

The API will be available at `http://localhost:8000`

#### Stop the application
```bash
docker-compose down
```

## Example Usage Scenario

### 1. Setup Operators
```bash
curl -X POST http://localhost:8000/operators \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "is_active": true, "max_load": 5}'

curl -X POST http://localhost:8000/operators \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob", "is_active": true, "max_load": 10}'
```

### 2. Create Source
```bash
curl -X POST http://localhost:8000/sources \
  -H "Content-Type: application/json" \
  -d '{"name": "Telegram Bot", "description": "Main support channel"}'
```

### 3. Configure Weights
```bash
curl -X POST http://localhost:8000/sources/1/weights \
  -H "Content-Type: application/json" \
  -d '[{"operator_id": 1, "weight": 30}, {"operator_id": 2, "weight": 70}]'
```

This means Alice gets ~30% of requests, Bob gets ~70%.

### 4. Register Requests
```bash
curl -X POST http://localhost:8000/requests \
  -H "Content-Type: application/json" \
  -d '{
    "lead_external_id": "customer_001",
    "source_id": 1,
    "message": "Need help with setup",
    "lead_name": "John Customer"
  }'
```

### 5. View Statistics
```bash
curl http://localhost:8000/requests/distribution/stats
```

## Project Structure

```
miniCRM/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # Database configuration
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py           # SQLAlchemy models
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic schemas
│   ├── api/
│   │   ├── __init__.py
│   │   ├── operators.py        # Operator endpoints
│   │   ├── sources.py          # Source endpoints
│   │   └── requests.py         # Request endpoints
│   └── services/
│       ├── __init__.py
│       └── distribution_service.py  # Distribution algorithm
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitignore
└── README.md
```

## Design Decisions

### 1. Load Definition
**Current load** = count of requests with `status = "active"`

This approach allows:
- Dynamic capacity management
- Operators can receive new work as they close requests
- Clear metric for monitoring operator workload

### 2. Distribution Algorithm
**Weighted random selection** was chosen for:
- Simplicity and transparency
- Statistical fairness over time
- No need to maintain complex state
- Easy to understand and debug

Alternative considered: Deterministic round-robin with weight tracking. This was not chosen to keep the implementation simple for a 1-2 hour task.

### 3. Handling No Available Operators
**Create request without assignment** approach:
- Pros: All requests are tracked; can analyze capacity issues; can manually assign later
- Cons: Requires monitoring for unassigned requests

### 4. Lead Identification
Uses `external_id` as the unique identifier:
- Allows integration with external systems
- One field for simplicity
- Could be extended to match by email/phone if needed

## Testing the System

### Test Weighted Distribution

1. Create 2 operators with weights 20 and 80
2. Create 100 requests
3. Check distribution statistics
4. Expected: ~20% to first operator, ~80% to second

### Test Load Limits

1. Create operator with max_load=2
2. Create 3 requests
3. After 2nd request: operator should receive no more
4. Update one request to "closed"
5. Create another request: should go to operator

### Test Multiple Sources

1. Create operator with weight 100 for source A, weight 0 for source B
2. Create request from source A: should assign operator
3. Create request from source B: should NOT assign operator

