# AI Ops Dashboard (Prototype)

Ask a business question in plain English, get back the right chart — automatically.

This is an early prototype that connects a natural-language question to a Postgres database, generates a safe SQL query, executes it, and returns a ready-to-render chart along with a plain-language takeaway. No manual SQL required.

> **Status:** working local Python prototype (not yet a deployed app/UI).

---

## Example

**Question:** `how many products are in each category?`

**Output:**
```json
{
  "type": "bar",
  "labels": ["Beauty & Personal Care", "Books & Stationery", "Electronics", ...],
  "values": [25, 25, 25, ...],
  "label_field": "category_name",
  "value_field": "product_count",
  "takeaway": "All categories currently have an equal number of products (25 each)."
}
```

---

## How it works

The pipeline is built as a [LangGraph](https://github.com/langchain-ai/langgraph) graph — each step is a node, with a retry loop when SQL execution fails.

```
question
   ↓
retrieve schema context (pgvector RAG)
   ↓
generate SQL (LLM)
   ↓
execute SQL (read-only DB user, validated)
   ↓
 [success] ──────────────→ build chart + takeaway
   ↓ [failure]
 fix SQL using the DB error message
   ↓
 retry execution
```

### Components

| Step | File | Responsibility | Uses LLM? |
|---|---|---|---|
| Schema retrieval | `rag_retriever.py` | Embeds table/column descriptions with pgvector, retrieves relevant schema context for a question | No (embedding only) |
| SQL generation | `sql_generator_agent.py` | Turns a question + schema context into a validated `SELECT` query | Yes |
| SQL execution | `sql_executor_agent.py` | Runs SQL against a read-only connection, rejects anything unsafe | No |
| SQL repair | `fix_sql.py` | Regenerates broken SQL using the actual Postgres error message | Yes |
| Chart generation | `chart_agent.py` | Picks chart type from result shape, builds a frontend-ready spec, generates a one-line insight | Mostly no (one small LLM call for the takeaway) |
| Orchestration | `main.py` | Wires all of the above into a LangGraph pipeline | — |

### Safety measures

- SQL execution uses a **dedicated read-only Postgres role** — never the app's write-capable user
- Every generated query is checked: must start with `SELECT`, and is rejected if it contains `INSERT`/`UPDATE`/`DELETE`/`DROP`/etc.
- Failed queries don't crash the pipeline — the error is fed back to the model for a self-correction attempt before giving up

---

## Chart type selection

| Result shape | Chart type |
|---|---|
| Single row, single value | Text summary |
| Contains a date/time column | Line chart |
| Multiple categories, ≤ 6 rows | Pie chart |
| Multiple categories, > 6 rows | Bar chart |

---

## Tech stack

- **LangGraph** — pipeline orchestration and the retry loop
- **Ollama** (`llama3.2:3b`, `nomic-embed-text`) — local LLM for SQL generation/repair and embeddings
- **pgvector** — schema embeddings stored directly in Postgres
- **psycopg** — direct, validated SQL execution
- **matplotlib** — local chart preview rendering (for testing; a real frontend would consume the JSON chart spec instead)
