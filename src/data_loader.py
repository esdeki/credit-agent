import pandas as pd
from pathlib import Path


def load_financial_data():
    """Load the financial ratios CSV file."""

    data_path = Path(__file__).parent.parent / "data" / \
        "companies_financial_ratios.csv"

    df = pd.read_csv(data_path)

    return df
