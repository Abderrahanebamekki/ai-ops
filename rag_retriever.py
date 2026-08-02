from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector

embeddings = OllamaEmbeddings(model="nomic-embed-text")

connection_string = "postgresql+psycopg://myuser:12345678@localhost:5432/mydb"

vectorstore = PGVector(
    embeddings=embeddings,
    collection_name="schema_chunks",
    connection=connection_string,
)


def get_relevant_chunks(question: str, k: int = 3):
  
    results = vectorstore.similarity_search_with_score(question, k=k)

    chunks = []
    for doc, score in results:
        chunks.append({
            "content": doc.page_content,
            "table": doc.metadata.get("table"),
            "score": score
        })
    return chunks


