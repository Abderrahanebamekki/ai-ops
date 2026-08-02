from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document


loader = PyPDFLoader("store_schema_chunks.pdf")
pages = loader.load()
document = "\n".join(p.page_content for p in pages)

raw_chunks = document.split("Table: ")[1:]  

documents = []
for raw in raw_chunks:
    table_name = raw.split("\n")[0].strip()
    content = "Table: " + raw.strip()
    documents.append(
        Document(page_content=content, metadata={"table": table_name})
    )

embeddings = OllamaEmbeddings(model="nomic-embed-text")

connection_string = "postgresql+psycopg://myuser:12345678@localhost:5432/mydb"

vectorstore = PGVector.from_documents(
    documents=documents,
    embedding=embeddings,
    collection_name="schema_chunks",
    connection=connection_string,
)
