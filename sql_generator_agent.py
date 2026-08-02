from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3.2:3b")  # or whichever model you're using

SQL_GEN_PROMPT = """You are a PostgreSQL expert. Given the schema context below,
write ONE read-only SELECT query that answers the question.

Rules:
- Only SELECT statements, never INSERT/UPDATE/DELETE/DROP
- Always add a LIMIT (max 500 rows) unless the question needs an aggregate
- Use only the tables/columns shown in the context below
- If using GROUP BY, every selected column must either be in the GROUP BY clause or wrapped in an aggregate function (SUM, COUNT, AVG, etc.)
- Double check the query is valid PostgreSQL syntax before returning it

Schema context:
{context}

Question: {question}

SQL:"""

def generate_sql(question: str, context_chunks: list) -> str:
    """
    Takes a question + retrieved schema chunks, returns a SQL string.
    Does NOT touch the database.
    """
    context = "\n\n".join(chunk["content"] for chunk in context_chunks)
    

    prompt = SQL_GEN_PROMPT.format(context=context, question=question)
    response = llm.invoke(prompt)
    sql = response.content.strip().strip("```sql").strip("```").strip()
    return sql