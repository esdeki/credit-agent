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

        # ۱. پیمایش فایل به فایل ///
        # منظور از «فایل» در این عبارت، تک‌تک فایل‌های متنی موجود در پوشهٔ دانش (knowledge) است.
        # فقط فایل متنی را می خواند نه پی دی اف
        for file in self.knowledge_path.glob("*.txt"):

            with open(file, "r", encoding="utf-8") as f:
                content = f.read()  # ۲. خواندن کل متن همان فایل

            content_lower = content.lower()

            if normalized_company and normalized_company not in content_lower:  # ۳. شرط مورد نظر شما:
                continue  # رفتن به فایل بعدی بدون ذخیره این فایل

            if any(word in content_lower for word in query_words):
                documents.append({
                    "source": file.name,
                    "content": content
                })

        return documents


"""
نقاط قوت:

ساده، بدون نیاز به نصب کتابخانه‌های سنگین و بدون هزینه API.

برای پروژه‌های کوچک با چند فایل متنی محدود عالی و بسیار سریع کار می‌کند.

نقاط ضعف و محدودیت‌ها:

عدم درک معنایی (Semantic Search): این کد فقط بر اساس «کلمات مطابقت‌یافته» کار می‌کند. اگر کاربر بپرسد "وضعیت بدهی چطور است؟" و فایل متنی از کلمه "تعهدات مالی" استفاده کرده باشد، این کد آن را پیدا نمی‌کند.

عدم چک کردن استاپ‌وردهای فارسی (Stop Words): کلماتی مثل "است"، "در"، "که" طولشان بیشتر از ۱ حرف است؛ بنابراین وارد query_words می‌شوند و ممکن است فایل‌های کاملاً بی‌ربط را فقط به خاطر داشتن کلمه "است" انتخاب کنند.

حجم بالای خروجی: کل متن فایل (content) را برمی‌گرداند. اگر یک فایل ۱۰۰ صفحه باشد، کل آن وارد پرامپت می‌شود و توکن‌های LLM را می‌سوزاند (چانک‌بندی یا Chunking ندارد).

همان‌طور که برنامه‌نویس خودش در Docstring کد کامنت گذاشته (no embeddings yet)، این نسخه فعلاً یک نسخه پایه (Version 0.1 / Mock) است و در آینده باید با پایگاه‌داده برداری (Vector DB مثل FAISS یا ChromaDB) جایگزین شود.
"""

"""
کدی که با هم بررسی کردیم، از ساده‌ترین حالت ممکن (Exact Keyword Matching) استفاده کرده و هنوز تبدیل به یک سیستم RAG واقعی بر پایه معنا نشده است.
"""

"""
چرا این کد فعلی دچار خطا می‌شود؟ (محدودیت‌های کد موجود)
حذف اطلاعات غیرمستقیم اما مهم:
همان‌طور که گفتید، ممکن است فایلی درباره "دستورالعمل ارزیابی مخاطره صنعت حمل‌ونقل" در پوشه دانش باشد. این فایل کلمه «تپسی» را ندارد، اما اطلاعات آن برای تحلیل اعتباری تپسی بسیار حیاتی است! کد فعلی این فایل را کلاً رد می‌کند چون فقط نام شرکت را جستجو می‌کند.

وابستگی به تطابق کلمه‌ای دقیق (Literal Matching):
اگر در فایل نوشته شده باشد "شرکت پیشگامان پالایش نوین" اما کاربر جستجو کند "پالایش نوین" یا نام برند تجاری را ببرد، کد آن را پیدا نمی‌کند.

نبود مفهوم «شباهت معنایی» (Semantic Similarity):
سیستم فعلی برداری (Vector/Embedding) ندارد؛ بنابراین نمی‌تواند بفهمد که «ریسک نکول» و «عدم توانایی در پرداخت تسهیلات» یک مفهوم دارند.
"""
