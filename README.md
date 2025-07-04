


```markdown
# 🧠 Natural Language Analytics

A full-stack, containerized system that lets users upload raw tabular data (CSV/XLSX), auto-generate semantic metadata and metrics, and query the data using natural language (NL). Powered by LLMs, LangChain, Streamlit, and FastAPI.

## 🚀 Features

- 📥 Upload CSV or Excel files for ingestion
- 🔍 Automatic extraction of column metadata (type, name, etc.)
- 🧠 GPT-powered column dictionary creation
- 📊 Auto-generated metrics based on heuristics (SUM, AVG, counts, etc.)
- 💬 Ask natural language questions → get SQL + answers
- 📈 Streamlit frontend with visualizations and step tracking
- 🔄 Hot-reloading dev environment with Docker Compose

---

## 📦 Architecture

```

```
         ┌──────────────┐
         │  Streamlit   │ ◄────── User uploads, queries
         └─────┬────────┘
               │
        REST API Calls
               │
      ┌────────▼────────┐
      │    FastAPI      │ ◄───── `/ingest`, `/metrics`, `/query`
      └────────┬────────┘
               │
     LangGraph Pipeline
               │
```

┌────────┬────────┴────────┬────────┐
│        │                 │        │
▼        ▼                 ▼        ▼
Extractor  →  Dictionary Agent  →  Analyst Agent
(sqlalchemy)   (OpenAI GPT-4o)   (heuristics → metrics)

```

---

## 📂 Project Structure

```

.
├── backend
│   ├── agents/             # Core agent logic (extractor, GPT dictionary, metrics)
│   ├── db.py               # Async SQLAlchemy DB session
│   ├── models.py           # ORM Models: ColumnMeta, Dictionary, Metrics, etc.
│   ├── graph.py            # LangGraph pipeline setup
│   ├── ingestor.py         # File ingestion logic (create/replace/append)
│   ├── main.py             # FastAPI server
│   ├── create\_tables.py    # Manual DB init script
│   ├── migrations/         # Alembic migration scripts
│   └── requirements.txt
├── frontend
│   ├── app.py              # Streamlit frontend
│   └── requirements.txt
├── docker-compose.yml      # Dev environment with Postgres, Backend, Frontend
└── .env                    # Secrets and DB config

````

---

## 🛠️ Tech Stack

| Layer     | Tech                     |
|-----------|--------------------------|
| Backend   | Python, FastAPI, SQLAlchemy, LangChain, Alembic |
| Frontend  | Streamlit + Plotly       |
| LLMs      | OpenAI GPT-4o (via API)  |
| DB        | PostgreSQL               |
| DevOps    | Docker, Docker Compose   |

---

## 📌 Setup Instructions

1. **Clone the Repo**

```bash
git clone https://github.com/your-username/natural-language-analytics.git
cd natural-language-analytics
````

2. **Set Environment Variables**

Create a `.env` file in the root of the project with the following:

```env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/analytics_db
API_BASE=http://backend:8000
```

3. **Run with Docker Compose**

```bash
docker-compose up --build
```

* Streamlit UI: [http://localhost:8501](http://localhost:8501)
* FastAPI backend: [http://localhost:8000/docs](http://localhost:8000/docs)
* PostgreSQL: localhost:5432

---

## 🧪 Example Flow

1. **Upload** a CSV or Excel file (Tab 1).
2. **Watch** as the system:

   * Extracts schema & types
   * Generates descriptions (GPT)
   * Computes metrics (sum, avg, counts)
3. **Explore** metrics (Tab 2).
4. **Ask** questions in plain English (Tab 3):

   * *"What is the average order amount per customer?"*
   * *"Show top 10 countries by transaction count"*

---

## 📈 Sample Metric JSON Output

```json
{
  "metric_name": "orders.amount_avg",
  "sql_definition": "SELECT AVG(\"amount\") AS \"avg_amount\" FROM \"orders\"",
  "viz_hint": {
    "x": null,
    "y": "avg_amount",
    "type": "numeric"
  },
  "tags": ["orders", "amount", "avg"]
}
```

---

## 🧪 Developer Tips

* You can trigger ingestion directly with: `curl -F 'file=@file.csv' http://localhost:8000/ingest/`
* Use `create_tables.py` to bootstrap your DB schema
* Modify `query_runner.py` if you want to switch LLM providers or prompts

---

## 🧾 License

MIT License © 2025 \[Your Name]

---

## 🙌 Acknowledgements

* [LangChain](https://www.langchain.com/)
* [OpenAI](https://openai.com/)
* [Streamlit](https://streamlit.io/)
* [SQLAlchemy](https://www.sqlalchemy.org/)

