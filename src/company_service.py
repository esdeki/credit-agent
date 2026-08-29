from src.exceptions import CompanyNotFoundError


def get_company_data(df, company_name):
    """
    Return financial data for a selected company.
    Raises:
    CompanyNotFoundError: اگر شرکتی با این نام در داده وجود نداشته باشد.
    """

    company_data = df[df["Company_Name"] == company_name]
    if company_data.empty:
        raise CompanyNotFoundError(
            f"اطلاعاتی برای شرکت «{company_name}» در داده‌ها یافت نشد."
        )

    return company_data
