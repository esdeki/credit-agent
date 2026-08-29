def analyze_company(company_data):
    """
    Analyze the financial ratios of a company.
    """

    analysis = {
        "Current_Ratio_Average": company_data["Current_Ratio"].mean(),
        "Quick_Ratio_Average": company_data["Quick_Ratio"].mean(),
        "Debt_Ratio_Average": company_data["Debt_Ratio"].mean(),
    }

    return analysis
