from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from rag_retriever import get_relevant_chunks     # your pgvector function
from sql_generator_agent import generate_sql
from sql_executor_agent import execute_sql
from chart_agent import build_chart , render_preview_image
from fix_sql import regenerate_sql

from dotenv import load_dotenv

load_dotenv()

READONLY_CONN = "postgresql://readonly_user:12345678@localhost:5432/mydb"

# ---------- 1. Define the shared state ----------
class PipelineState(TypedDict):
    question: str
    chunks: Optional[list]
    sql: Optional[str]
    rows: Optional[list]
    chart: Optional[dict]
    error: Optional[str]    
    attempts: int


# ---------- 2. Define each node (one function per agent) ----------
def retrieve_node(state: PipelineState) -> PipelineState:
    state["chunks"] = get_relevant_chunks(state["question"])
    return state

def generate_sql_node(state: PipelineState) -> PipelineState:
    state["sql"] = generate_sql(state["question"], state["chunks"])
    return state

def execute_sql_node(state: PipelineState) -> PipelineState:
    try:
        state["rows"] = execute_sql(state["sql"], READONLY_CONN)
        state["error"] = None
    except Exception as e:
        state["error"] = str(e)
        state["rows"] = None
    return state

def chart_node(state: PipelineState) -> PipelineState:
    if state["rows"] is None:
        state["chart"] = {"type": "error", "message": f"Query failed: {state['error']}"}
        return state
    state["chart"] = build_chart(state["question"], state["rows"])
    return state


def fix_sql_node(state: PipelineState) -> PipelineState:
    state["sql"] = regenerate_sql(state["question"] ,state["sql"] , state["error"])
   
    return state


# ---------- 3. Build the graph: straight line, no branches ----------
graph = StateGraph(PipelineState)


graph.add_node("retrieve", retrieve_node)
graph.add_node("generate_sql", generate_sql_node)
graph.add_node("execute_sql", execute_sql_node)
graph.add_node("fix_sql", fix_sql_node)
graph.add_node("execute_sql_retry", execute_sql_node)   # same function, second node name
graph.add_node("build_chart", chart_node)

graph.set_entry_point("retrieve")
graph.add_edge("retrieve", "generate_sql")
graph.add_edge("generate_sql", "execute_sql")
graph.add_edge("execute_sql", "fix_sql")
graph.add_edge("fix_sql", "execute_sql_retry")
graph.add_edge("execute_sql_retry", "build_chart")
graph.add_edge("build_chart", END)

app = graph.compile()


if __name__ == "__main__":
    result = app.invoke({"question": "how many products are in each category?", "attempts": 0})
    chart = result["chart"]
    print(chart)

    image_path = render_preview_image(chart, output_path="preview.png")
    if image_path:
        print(f"Chart image saved to: {image_path}")
    else:
        print("No image generated (text-only result, nothing to render)")