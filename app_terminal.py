# This file is the terminal version of the Credit Agent.
# It is kept for learning and testing the Agent pipeline without UI.

from src.financial_analyzer import analyze_company
from src.data_loader import load_financial_data
from src.company_service import get_company_data
from src.credit_agent import create_credit_report
from src.credit_rules import evaluate_credit_rules

df = load_financial_data()
company_name = input("Enter company name: ")

company_data = get_company_data(df, company_name)
analysis = analyze_company(company_data)
rule_result = evaluate_credit_rules(analysis)
report = create_credit_report(company_name, analysis, rule_result)
print(report)
