from langchain_ollama import ChatOllama
import re


llm = ChatOllama(model="llama3.2:3b")  # or whichever model you're using

FIX_SQL_PROMPT = """This PostgreSQL query failed.

Question: {question}
Broken SQL: {sql}
Error: {error}

Fix the query. Return ONLY the corrected SQL, no explanation."""


def clean_sql(raw: str) -> str:
    # Remove ```sql or ``` fences anywhere, opening or closing
    cleaned = re.sub(r"```sql|```", "", raw)
    return cleaned.strip()

def regenerate_sql(question: str, sql: str , error:str ) -> str:
 
    

    prompt = FIX_SQL_PROMPT.format(sql=sql, question=question ,error=error)
    response = llm.invoke(prompt)
    sql = clean_sql(response.content)
    return sql