# 🛡️ RetireIQ: Bank-Grade Agentic AI for Retirement

RetireIQ is a modern, high-security conversational intelligence platform designed to revolutionize retirement planning. It bridges the gap between complex financial data and natural language interaction using a "Local-First, Cloud-Scale" architecture.

![RetireIQ System Architecture](docs/gcp_architecture_v2.png)

---

## 🏛️ Architecture & Vision
Built with an **Application Factory** pattern, RetireIQ is designed for modularity, security, and scalability.

- **Agentic Core**: Specialized agents (Knowledge, Portfolio, Transaction) orchestrated by a high-speed semantic router.
- **Leak-Proof Security**: Strict PII sanitization and re-hydration proxy layers to ensure financial data never leaves your control.
- **RAG Ecosystem**: High-fidelity retrieval augmented generation powered by `pgvector` and Vertex AI.

### 📜 Technical Deep-Dives
- [Target State Vision](docs/target_state_vision.md) — The ultimate architectural goal.
- [GCP System Design](docs/system_design_gcp.md) — Enterprise-scale cloud mapping.
- [Leak-Proof Security Strategy](docs/security.md) — Our approach to "Bank-Grade" data handling.
- [Master Roadmap](docs/todo_plan.md) — Phased implementation tracking.

---

## 🚀 Getting Started (Local Core)
RetireIQ is optimized for **Local-First** development. You can spin up the entire ecosystem on your Mac in minutes.

### Prerequisites
- **Docker** & **Docker Compose**
- **Make**
- **Ollama** (for local LLM power)

### Quick Setup
```bash
# 1. Clone the repo and set up your config
cp .env.example .env

# 2. Launch the infrastructure (API + pgvector Database)
make up

# 3. Monitor the agentic logic
make logs
```

For detailed setup instructions and database migration guides, see [Documentation: Setup Instructions](docs/setup-instructions.md).

---

## 🛠️ Built By
**Architected & Developed by:** [sumitsr](https://github.com/sumitsr)

---

## 📜 License
This project is proprietary and confidential. Unauthorized copying of this file, via any medium, is strictly prohibited.
