import matplotlib.pyplot as plt
from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3.2:3b")


def decide_chart_type(rows: list[dict]) -> str:
    """
    Looks at the shape of the query result and picks the right chart type.
    Returns: 'text', 'line', 'bar', or 'pie'
    """
    if not rows:
        return "text"

    num_rows = len(rows)
    columns = list(rows[0].keys())

    # single row, single value -> just text, no chart needed
    if num_rows == 1 and len(columns) <= 2:
        return "text"

    # look for a date/time-like column -> time series -> line chart
    date_keywords = ["date", "time", "created_at", "placed_at", "month", "day"]
    has_date_col = any(any(k in col.lower() for k in date_keywords) for col in columns)
    if has_date_col:
        return "line"

    # few categories -> pie chart is readable; many -> bar chart
    if num_rows <= 6:
        return "pie"

    return "bar"


def generate_chart_spec(rows: list[dict], chart_type: str) -> dict:
    """
    Builds a frontend-ready chart spec (JSON) for Angular (ngx-charts/Chart.js style).
    No image rendering here -- just structured data + type.
    """
    if chart_type == "text":
        value = list(rows[0].values())[0] if rows else None
        return {"type": "text", "value": value}

    columns = list(rows[0].keys())
    label_col, value_col = columns[0], columns[1]

    return {
        "type": chart_type,
        "labels": [str(r[label_col]) for r in rows],
        "values": [r[value_col] for r in rows],
        "label_field": label_col,
        "value_field": value_col,
    }


def generate_takeaway(question: str, rows: list[dict]) -> str:
    """
    One LLM call: turns the raw result into a one-line plain-language insight.
    This is the only part of this agent that actually needs reasoning.
    """
    prompt = f"""Question: {question}
Data: {rows[:10]}

Write ONE short sentence (max 20 words) summarizing the key insight. No explanation, just the sentence."""
    response = llm.invoke(prompt)
    return response.content.strip()


def render_preview_image(spec: dict, output_path: str = "preview.png"):
    """
    Optional: renders an actual image, useful for local testing/debugging
    before wiring up the real Angular frontend.
    """
    if spec["type"] == "text":
        return None

    fig, ax = plt.subplots(figsize=(6, 4))

    if spec["type"] == "line":
        ax.plot(spec["labels"], spec["values"], marker="o")
    elif spec["type"] == "bar":
        ax.bar(spec["labels"], spec["values"])
    elif spec["type"] == "pie":
        ax.pie(spec["values"], labels=spec["labels"], autopct="%1.1f%%")

    ax.set_title(spec.get("value_field", ""))
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    return output_path


def build_chart(question: str, rows: list[dict]) -> dict:
    """
    Main entry point -- combines everything above.
    """
    chart_type = decide_chart_type(rows)
    spec = generate_chart_spec(rows, chart_type)
    spec["takeaway"] = generate_takeaway(question, rows)
    return spec