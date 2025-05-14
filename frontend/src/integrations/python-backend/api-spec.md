
# RetireIQ Python Backend API Specification

## Overview
This document outlines the API endpoints that need to be implemented in the separate Python backend for RetireIQ. The backend should be built using Flask or FastAPI and deployed separately.

## Base URL
When deployed, the API will be accessible at: `https://your-python-api-url.com/api`

## Authentication
All API endpoints require authentication using bearer tokens except for the login and register endpoints.

## Endpoints

### Authentication

#### POST /auth/register
Register a new user.
```
Request:
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "User Name"
}

Response:
{
  "user_id": "uuid",
  "email": "user@example.com",
  "name": "User Name",
  "token": "jwt_token"
}
```

#### POST /auth/login
Log in an existing user.
```
Request:
{
  "email": "user@example.com",
  "password": "securepassword"
}

Response:
{
  "user_id": "uuid",
  "email": "user@example.com",
  "name": "User Name",
  "token": "jwt_token"
}
```

### User Profile

#### GET /profile
Get the current user's profile.
```
Response:
{
  "user_id": "uuid",
  "email": "user@example.com",
  "name": "User Name",
  "age": 35,
  "retirementAge": 65,
  "currentSavings": 100000,
  "monthlySavings": 1000,
  "riskTolerance": "medium"
}
```

#### PUT /profile
Update the current user's profile.
```
Request:
{
  "age": 35,
  "retirementAge": 65,
  "currentSavings": 100000,
  "monthlySavings": 1000,
  "riskTolerance": "medium"
}

Response:
{
  "user_id": "uuid",
  "email": "user@example.com",
  "name": "User Name",
  "age": 35,
  "retirementAge": 65,
  "currentSavings": 100000,
  "monthlySavings": 1000,
  "riskTolerance": "medium"
}
```

### Chat

#### POST /chat/message
Send a message to the chat assistant.
```
Request:
{
  "message": "How much should I save for retirement?",
  "conversation_id": "uuid" (optional - if continuing a conversation)
}

Response:
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "response": "Based on your profile information...",
  "suggested_questions": [
    {
      "id": "1",
      "text": "What are the benefits of a Roth IRA?",
      "category": "investment"
    },
    {
      "id": "2",
      "text": "How much do I need to save monthly?",
      "category": "planning"
    }
  ]
}
```

#### GET /chat/history
Get chat history for a conversation.
```
Request Parameters:
conversation_id=uuid

Response:
{
  "conversation_id": "uuid",
  "messages": [
    {
      "id": "uuid",
      "content": "How much should I save for retirement?",
      "type": "user",
      "timestamp": "2023-05-12T15:30:45Z"
    },
    {
      "id": "uuid",
      "content": "Based on your profile information...",
      "type": "bot",
      "timestamp": "2023-05-12T15:30:48Z"
    }
  ]
}
```

### Model Configuration

#### GET /config/llm
Get the current LLM configuration.
```
Response:
{
  "provider": "openai",
  "modelName": "gpt-4o",
  "temperature": 0.7
}
```

#### PUT /config/llm
Update the LLM configuration.
```
Request:
{
  "provider": "anthropic",
  "modelName": "claude-3-sonnet",
  "temperature": 0.5
}

Response:
{
  "provider": "anthropic",
  "modelName": "claude-3-sonnet",
  "temperature": 0.5
}
```

## Python Implementation Requirements

### Technology Stack
- Flask or FastAPI framework
- PostgreSQL database
- JWT for authentication
- OpenAI, Anthropic, or Perplexity APIs for AI responses
- CORS support for frontend integration

### Key Components
1. Authentication service
2. User profile service
3. Chat service with LLM integration
4. Configuration service

### Deployment
The API should be containerized using Docker and can be deployed to platforms like:
- AWS (ECS, Lambda)
- Google Cloud Run
- Heroku
- Digital Ocean App Platform
