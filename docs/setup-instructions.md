# Step-by-step Setup Instructions

These instructions guide you through setting up the RetireIQ application on your local machine for development and testing.

## Prerequisites
Ensure the following tools are installed on your machine:
- **Python 3.10+**
- **Docker** and **Docker Compose**
- **PostgreSQL** (if you prefer running it locally outside of Docker)
- **Make** (`Makefile` contains convenient shorthand commands)

## 1. Clone & Set Up the Environment

First, open your terminal and set up a clean Python virtual environment.

```bash
# Clone your repository (if not already done)
git clone <your-retireiq-remote-url>
cd retireiq

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install the dependencies
pip install -r requirements.txt
```

## 2. Configure Environment Variables
You will need secrets like database connection strings and LLM API keys.

```bash
cp .env.example .env
```
Open the `.env` file and verify or change your placeholders:
- `DATABASE_URL=postgresql://user:password@localhost:5432/retireiq`
- `OPENAI_API_KEY=your_key_here`

## 3. Database Initializations and Migrations
Apply schemas to your relational database and port over any legacy JSON data. Ensure your Postgre DB is running.

```bash
# Apply alembic/SQLAlchemy migrations
flask db upgrade

# Run custom seed scripts if you are migrating the old JSON system
flask seed db
```

## 4. Run the Application locally
Now start your Flask development server:

```bash
python run.py
```
*The API will be available at `http://127.0.0.1:5000`.*

### Running via Docker
If you prefer a clean containerized environment:
```bash
docker build -t retireiq .
docker run -p 5000:5000 --env-file .env retireiq
```

## 5. Development Utilities

```bash
# Run unit tests
pytest tests/

# Check styling and lints
ruff check .
```
