from math import isfinite
from pydantic import BaseModel, ConfigDict, Field


class RetentionOffer(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    discount_percent: float = Field(ge=0, le=100, allow_inf_nan=False)
    free_months: int = Field(ge=0)
    bonus_value_usd: float = Field(ge=0, allow_inf_nan=False)
    explanation: str = Field(min_length=1, max_length=1000)


def validate_offer(risk: float, proposal: dict) -> dict:
    if not isfinite(risk) or not 0 <= risk <= 1:
        raise ValueError("Invalid churn risk.")

    offer = RetentionOffer.model_validate(proposal)

    if risk < 0.7 and offer.discount_percent > 20:
        return {
            "status": "blocked",
            "reason": "Discount above 20% forbidden for risk below 0.7.",
        }

    reasons = []
    if offer.free_months > 3:
        reasons.append("Free service exceeds 3 months.")
    if offer.bonus_value_usd > 500:
        reasons.append("Total bonus exceeds $500.")

    if reasons:
        return {
            "status": "manual_review_required",
            "reasons": reasons,
            "proposal": offer.model_dump(),
            "approved_for_customer": False,
        }

    return {
        "status": "approved",
        "offer": offer.model_dump(),
        "approved_for_customer": True,
    }


if __name__ == "__main__":
    base = {
        "discount_percent": 10.0,
        "free_months": 0,
        "bonus_value_usd": 0.0,
        "explanation": "Offer a loyalty discount.",
    }

    cases = [
        ("Normal offer", 0.1, base, "approved"),
        ("Unauthorized discount", 0.1,
         {**base, "discount_percent": 30.0}, "blocked"),
        ("High-risk discount", 0.95,
         {**base, "discount_percent": 30.0}, "approved"),
        ("Long free service", 0.95,
         {**base, "free_months": 4}, "manual_review_required"),
        ("Large bonus", 0.95,
         {**base, "bonus_value_usd": 501.0}, "manual_review_required"),
    ]

    for name, risk, proposal, expected in cases:
        result = validate_offer(risk, proposal)
        assert result["status"] == expected, (name, result)
        print(f"PASS: {name} -> {result['status']}")

    print("POLICY CHECK PASSED")
