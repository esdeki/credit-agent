import pandas as pd


NON_PERIOD_MARKERS = (
    "درصد تغيير",
    "درصد تغییر",
    "درصد تغييرات",
    "درصد تغییرات",
    "میانگین",
    "ميانگين",
    "جمع",
    "total",
    "average",
)


def _is_valid_period(label):
    if not isinstance(label, str):
        return False
    normalized = " ".join(label.split()).strip().lower()
    if not normalized:
        return False
    return not any(marker in normalized for marker in NON_PERIOD_MARKERS)


def _safe_mean(series):
    numeric = pd.to_numeric(series, errors="coerce")
    filtered = numeric.dropna()
    if filtered.empty:
        return None
    return filtered.mean()


def analyze_company(company_data):
    """Analyse financial ratios using only valid period rows."""

    if company_data is None or company_data.empty:
        return {}

    if "Period_Date" in company_data.columns:
        filtered = company_data[company_data["Period_Date"].apply(
            _is_valid_period)]
    else:
        filtered = company_data.copy()

    ratios = {
        "Current_Ratio_Average": _safe_mean(filtered.get("Current_Ratio")),
        "Quick_Ratio_Average": _safe_mean(filtered.get("Quick_Ratio")),
        "Debt_Ratio_Average": _safe_mean(filtered.get("Debt_Ratio")),
    }

    return {k: v for k, v in ratios.items() if v is not None}


"""
با استفاده از تابع _safe_mean میانگین ۳ شاخص بسیار حیاتی مالی را محاسبه می‌کند:

Current_Ratio (نسبت جاری): توانایی شرکت در پرداخت دیون کوتاه مدت.

Quick_Ratio (نسبت سریع): نقدشوندگی سریع شرکت بدون احتساب موجودی کالا.

Debt_Ratio (نسبت بدهی): میزان وابستگی دارایی‌های شرکت به بدهی‌ها.
"""
