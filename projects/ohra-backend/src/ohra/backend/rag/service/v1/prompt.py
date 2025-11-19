from langchain_core.prompts import PromptTemplate
from typing import List
from .schema import RetrievedDocument


def format_context_docs(context_docs: List[RetrievedDocument], max_content_length: int = 2000) -> str:
    contents = []
    for doc in context_docs:
        if content := doc.content:
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            parts = [f"<title>{doc.title}</title>", f"<content>{content}</content>"]
            if url := doc.metadata.get("url"):
                parts.append(f"<url>{url}</url>")
            contents.append("<document>\n" + "\n".join(parts) + "\n</document>")

    return "\n\n".join(contents) if contents else "제공된 문서가 없습니다."


__SYSTEM_PROMPT__ = """You are OHRA, an AI assistant for AHA&Company.

Answer the user's question directly and concisely.

Rules:
1. Answer the question first, then provide context if needed.
2. Only reference previous conversation if it is explicitly provided in the message history.
3. When using information from documents, ALWAYS cite the source using the <title> and <url> tags
   provided in the document.
4. Only use the provided documents if they are DIRECTLY relevant to answering the question.
5. If documents are not relevant, ignore them completely and answer based on your knowledge.
6. For AHA&Company related questions, you can use general knowledge if documents are not available or not relevant.
7. Do not make up or assume previous conversations that are not in the message history.
8. If the question asks about conversation context (e.g., "우리 무슨 얘기하고 있어"),
   use the message history, not documents."""

__PROMPT_TEMPLATE__ = PromptTemplate(
    template="""Reference documents (only use if directly relevant):
{context}

Question: {question}

Answer the question directly and concisely.
- If you use information from the documents, cite the source using the <title> and <url> from the document tags.
- Format citations as: [title](url) if URL is available, or just "title" if no URL.
- If the documents are directly relevant, use them to provide an accurate answer with proper citations.
- If the documents are NOT relevant, ignore them completely and answer based on your knowledge.""",
    input_variables=["context", "question"],
)
