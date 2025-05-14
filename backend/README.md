
# RetireIQ Python Backend

This is the Python backend for the RetireIQ retirement planning assistant application. It provides API endpoints for authentication, user profile management, chat functionality, and LLM configuration.

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
echo "ANTHROPIC_API_KEY=your-anthropic-api-key" >> .env
```

### Running the Server

To run the server in development mode:
```bash
python app.py
```

The API will be available at `http://localhost:5000/api`.

For production deployment, use Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API Documentation

The API provides the following endpoints:

### Authentication
- `POST /api/auth/register`: Register a new user
- `POST /api/auth/login`: Log in an existing user

### User Profile
- `GET /api/profile`: Get the current user's profile
- `PUT /api/profile`: Update the current user's profile

### Chat
- `POST /api/chat/message`: Send a message to the chat assistant
- `GET /api/chat/history`: Get chat history for a conversation

### Model Configuration
- `GET /api/config/llm`: Get the current LLM configuration
- `PUT /api/config/llm`: Update the LLM configuration

See the API specification file in the frontend project for detailed request and response formats.

## Deployment

For production deployment, consider using:
1. Docker containerization
2. Cloud hosting services like AWS, Google Cloud, or Heroku
3. Setting up proper authentication and security measures
4. Implementing a database backend (PostgreSQL, MongoDB, etc.)

## Extending the Application

This starter backend provides a foundation for building a more robust retirement planning assistant. Consider these enhancements:

1. Implement a proper database instead of in-memory storage
2. Add retirement calculation and modeling functionality
3. Integrate financial data providers for market information
4. Add multi-factor authentication
5. Implement rate limiting and other security measures
