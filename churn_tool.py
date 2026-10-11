from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def load_assets():
    model = joblib.load(ROOT / "models/churn_model.pkl")
    customers = pd.read_csv(ROOT / "data/telco_customers.csv")
    return model, customers


def get_customer_churn_risk(customer_id: str) -> dict:
    model, customers = load_assets()

    matches = customers.loc[
        customers["customerID"].astype(str) == str(customer_id)
    ]
    if len(matches) != 1:
        raise ValueError("Customer must exist and have a unique ID.")

    columns = list(model.feature_names_in_)
    if "Churn" in columns:
        raise ValueError("Target leakage detected.")

    features = matches.loc[:, columns].copy()
    for name in ("TotalCharges", "MonthlyCharges", "tenure", "SeniorCitizen"):
        if name in features:
            features[name] = pd.to_numeric(features[name], errors="raise")

    if features.isna().any().any():
        raise ValueError("Customer features contain missing values.")

    classes = list(model.classes_)
    churn_index = classes.index(1)
    risk = float(model.predict_proba(features)[0, churn_index])
    row = features.iloc[0]

    return {
        "churn_risk": round(risk, 4),
        "risk_level": "high" if risk >= 0.7 else "low",
        "monthly_charges": float(row["MonthlyCharges"]),
        "tenure_months": int(row["tenure"]),
        "contract": str(row["Contract"]),
        "reasoning_budget_usd": 0.15 if risk >= 0.7 else 0.05,
    }


if __name__ == "__main__":
    _, customers = load_assets()
    for customer_id in customers["customerID"].head(5):
        print(get_customer_churn_risk(str(customer_id)))
