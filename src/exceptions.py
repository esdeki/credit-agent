class CompanyNotFoundError(ValueError):
    """وقتی شرکت درخواستی در داده‌ها یافت نشود."""
    pass


class ReportGenerationError(ValueError):
    """وقتی مدل هوش مصنوعی نتواند گزارش معتبر تولید کند."""
    pass
