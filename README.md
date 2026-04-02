# RetireIQ Python Backend

This is the Python backend for the RetireIQ retirement planning assistant application. It provides API endpoints for authentication, user profile management, chat functionality, and smart product recommendations powered by AI agents.

## Architecture

The backend has recently been migrated to a modern, production-grade **Flask + SQLAlchemy Application Factory** architecture.

- `app/models/`: SQLAlchemy ORM models (`User`, `Product`, `Chat`).
- `app/routes/`: Flask Blueprints defining modular API endpoints.
- `app/services/`: Core logic abstractions for LLMs (`llm_service.py`), external agent APIs (`agent_service.py`), and the risk-scoring product engine (`recommender.py`).
- `app.db`: A local SQLite database designed to eventually be dropped-in via `DATABASE_URL` with a PostgreSQL server in production environments.

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create a .env file with the following variables
echo "JWT_SECRET_KEY=your-secure-jwt-secret" > .env
echo "OPENAI_API_KEY=your-openai-api-key" >> .env
echo "AZURE_OPENAI_API_KEY=your-azure-key" >> .env
echo "AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com" >> .env
echo "LIONIS_AGENT_TOKEN=your-agent-authorization-token" >> .env
echo "LIONIS_EVENT_TOKEN=your-event-authorization-token" >> .env
```

### Initializing the Database 
*Note: If you have already seeded your database, you can skip this.*

A utility script exists to scrape old `customer_data` and `products.json` formats and map them cleanly into SQLite:
```bash
python scripts/seed_db.py
```

### Running the Server

To run the server in development mode:
```bash
python run.py
```

The API will be available at `http://localhost:5000`.

For production deployment, use Gunicorn referencing the application factory:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

## API Documentation

### Authentication
- `POST /api/auth/register`: Register a new user
- `POST /api/auth/login`: Log in an existing user

### User Profile
- `GET /api/profile`: Get the authenticated user's profile
- `PUT /api/profile`: Update the authenticated user's profile
- `GET /api/unauth/profile?user_id=...`: Retrieve arbitrary user profile 

### AI Recommendations 
- `GET /api/recommend`: Get scored products for the active user
- `GET /api/unauth/recommend?user_id=...`: Get scored products based on a specific user's risk tolerance

### Chat & Agent
- `POST /api/chat/message`: Send a message to the AI retirement assistant. Coordinates internal OpenAI/Azure routing with Lionis agent services behind the scenes.

## Deployment

For production deployment, consider using:
1. Setting the `DATABASE_URL` environment variable for a managed database (PostgreSQL, MySQL).
2. Docker containerization.
3. Cloud hosting services like AWS, Google Cloud, or Heroku.
