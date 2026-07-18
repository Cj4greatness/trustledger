# TrustLedger

A transaction escrow and fulfillment tracker built for small business owners and their customers. TrustLedger sits between a business and a customer for a single transaction and tracks it through clearly enforced stages — **payment confirmed → shipped → delivered** — so nothing gets disputed later.

Built as a full-stack solo project: from an empty terminal to a containerized, multi-user SaaS product with AI-assisted operations.

## Features

- **Multi-user accounts** — each business owner signs up and only sees their own transactions
- **Enforced transaction workflow** — a state machine that refuses to let you skip steps (e.g. can't mark something "shipped" before payment is confirmed)
- **Full audit trail** — every status change is logged with a real timestamp, viewable per transaction
- **Wallet dashboard** — confirmed vs. pending totals per business owner
- **AI assistant** — natural-language chat interface (powered by the Claude API) that can create transactions and confirm payment/shipping/delivery through plain English
- **Auto-flagging** — transactions shipped but not delivered within a configurable window are automatically flagged as overdue
- **PDF invoices** — generated on demand with full transaction details and history
- **Live forex ticker** — real-time USD/NGN exchange rate
- **Dark/light mode** — glassmorphism UI with a persistent theme toggle

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy
- **Database:** PostgreSQL
- **Frontend:** Server-rendered Jinja2 templates, vanilla JS
- **AI:** Anthropic Claude API
- **PDF generation:** ReportLab
- **Auth:** Session-based, bcrypt password hashing
- **Containerization:** Docker, Docker Compose
- **Infrastructure (in progress):** Terraform, AWS (EKS, ECR, RDS), Kubernetes, Jenkins, Prometheus/Grafana

## Architecture
├── main.py              # FastAPI app, routes, business logic
├── models.py             # SQLAlchemy models (Transaction, User, TransactionEvent)
├── database.py            # DB connection/session setup
├── chatbot.py             # Claude API integration for the AI assistant
├── invoice.py             # PDF invoice generation
├── forex.py               # Cached USD/NGN exchange rate fetcher
├── auth_config.py         # Auth configuration
├── templates/              # Jinja2 HTML templates
├── static/                 # CSS + JS
├── Dockerfile
└── docker-compose.yml       # App + PostgreSQL, containerized
## Running Locally

### With Docker (recommended)

```bash
git clone https://github.com/Cj4greatness/trustledger.git
cd trustledger
cp .env.example .env   # add your own API keys
docker compose up --build
```

Visit `http://localhost:8000/signup` to create an account.

### Without Docker

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# set up a local PostgreSQL database and .env file (see .env.example)
uvicorn main:app --reload
```

## Environment Variables

See `.env.example` for the required keys:
- `DATABASE_URL`
- `SECRET_KEY`
- `ANTHROPIC_API_KEY`
- `EXCHANGE_RATE_API_KEY`

## Roadmap

- [x] Core transaction workflow + enforcement logic
- [x] Multi-user accounts with data isolation
- [x] AI chatbot integration
- [x] PDF invoices
- [x] Dockerized local development
- [ ] AWS infrastructure via Terraform (VPC, EKS, RDS)
- [ ] Kubernetes deployment
- [ ] CI/CD pipeline (Jenkins)
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Production domain + HTTPS

## Screenshots

<img width="1920" height="1080" alt="Screenshot (279)" src="https://github.com/user-attachments/assets/872031f8-8585-4b5b-abc0-0b2e5452a4d7" />
<img width="1920" height="1080" alt="Screenshot (278)" src="https://github.com/user-attachments/assets/f3a9e789-8e1a-4850-8370-571da31dc450" />
<img width="1920" height="1080" alt="Screenshot (277)" src="https://github.com/user-attachments/assets/67dbb790-4850-4642-8b3b-42ce95054756" />
<img width="1920" height="1080" alt="Screenshot (276)" src="https://github.com/user-attachments/assets/c0a917ba-2173-4dcd-ac38-3891a558bd5d" />
<img width="1920" height="1080" alt="Screenshot (275)" src="https://github.com/user-attachments/assets/6c8840ba-d54d-4fc4-a40d-7a4c76e0d856" />
<img width="1920" height="1080" alt="Screenshot (274)" src="https://github.com/user-attachments/assets/1c358fd9-10a3-48f6-9f26-7b5565947e3d" />
<img width="1920" height="1080" alt="Screenshot (273)" src="https://github.com/user-attachments/assets/509e4e00-0006-40e3-8c0b-2f8a13981b5b" />
<img width="1920" height="1080" alt="Screenshot (272)" src="https://github.com/user-attachments/assets/7659adb3-1175-4d33-8609-5fab21a3b829" />
<img width="1920" height="1080" alt="Screenshot (271)" src="https://github.com/user-attachments/assets/944fbb05-b79d-44bb-8906-23a5fb466d47" />
<img width="1920" height="1080" alt="Screenshot (270)" src="https://github.com/user-attachments/assets/4d5d78ce-e9be-4052-8967-95eb378fbf8b" />
<img width="1920" height="1080" alt="Screenshot (269)" src="https://github.com/user-attachments/assets/523f18d3-2509-49c6-b7a4-4a3aa663a154" />


## Author

Built by [Chisom Johnson](https://github.com/Cj4greatness) — Cloud DevOps Engineer.
