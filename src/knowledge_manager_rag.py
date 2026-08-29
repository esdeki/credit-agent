from pathlib import Path


class KnowledgeManager:
    """
    Manage external knowledge sources for RAG.
    """

    def __init__(self, knowledge_path=None):
        if knowledge_path is None:
            knowledge_path = Path(__file__).parent.parent / "knowledge"
        self.knowledge_path = Path(knowledge_path)

    def get_relevant_documents(self, query, company_name=None):
        """
        Retrieve documents whose content matches keywords from the query.

        Current version:
        Simple keyword filtering (no embeddings yet).

        Future version:
        Semantic Search (Embeddings + Vector Database).
        """

        documents = []

        if not self.knowledge_path.exists():
            return documents

        query_words = [  # این کد متن ورودی را به کلمات تشکیل‌دهنده‌اش خرد می‌کند و کلمات خیلی کوتاه (۲ حرف یا کمتر) را حذف می‌کند.
            word for word in query.lower().split()
            if len(word) > 1
        ]

        normalized_company = None
        if company_name:
            normalized_company = company_name.strip().lower()

        for file in self.knowledge_path.glob("*.txt"):

            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            content_lower = content.lower()

            if normalized_company and normalized_company not in content_lower:
                continue

            if any(word in content_lower for word in query_words):
                documents.append({
                    "source": file.name,
                    "content": content
                })

        return documents
