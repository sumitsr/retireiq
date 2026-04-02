# Security Strategy: Leak-Proof Configuration

RetireIQ implements a strict security boundary to ensure that "Bank-Grade" sensitive data is never committed to the source control repository.

## 1. Environment Variable Injection Strategy
All sensitive configuration (API Keys, Database Passwords, JWT Secrets) is injected at runtime using environment variables.

### How it Works:
- **Source**: Your private `.env` file (stored locally in the project root).
- **Orchestration**: `docker-compose.yml` utilizes variable interpolation (e.g., `${POSTGRES_PASSWORD}`) to pass these values from the host OS into the containers.
- **Application**: The Flask `Config` class fetches these values via `os.environ`.

---

## 2. Fail-Fast Mechanism
To prevent accidental insecure execution, the application is configured to **fail-fast**.

- If mandatory security keys (like `JWT_SECRET_KEY`) are missing from the environment, the application will raise a `RuntimeError` and refuse to start. 
- This ensures that a developer or an automated deployment is immediately alerted to a missing configuration before any traffic reaches the app.

---

## 3. Strict Source Protection
The repository is configured with a strict `.gitignore` policy:
- `.env` and all `.env.*` files are excluded.
- Only `.env.example` is committed, providing a template without actual values.

## 4. Best Practices for Contributors
- **Never hardcode strings**: Avoid using strings as fallbacks in `os.environ.get()`. If it's a secret, it should be mandatory.
- **Rotate Secrets Regularly**: In production environments, secrets should be rotated every 90 days.
- **Use Secret Management Tools**: For production deployments, we recommend using **Google Cloud Secret Manager** or **HashiCorp Vault**.

---

> [!CAUTION]
> **Data Leaks**: If you accidentally commit a secret to git, you MUST consider it compromised. Rotate the secret immediately and use a tool like `git-filter-repo` to scrub the history.
