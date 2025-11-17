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


__SYSTEM_PROMPT__ = """당신은 AI 어시스턴트 OHRA입니다.
질문에 직접적이고 간결하게 답변하세요.

답변 규칙:
1. 질문에 직접 답변을 먼저 제공하세요.
2. 이전 대화가 있는 경우에만 이전 대화 맥락을 고려하세요.
3. 제공된 문서가 질문과 관련이 있을 때만 인용하세요.
4. 문서 내용을 나열하지 말고, 필요한 부분만 간단히 언급하세요.
5. 아하앤컴퍼니 관련 질문은 문서가 없어도 일반 지식으로 답변할 수 있습니다."""

__PROMPT_TEMPLATE__ = PromptTemplate(
    template="""참고 문서:
{context}

질문: {question}

위 질문에 대해 직접적이고 간결하게 답변하세요. 문서가 질문과 관련이 없으면 무시하고 답변하세요.""",
    input_variables=["context", "question"],
)
