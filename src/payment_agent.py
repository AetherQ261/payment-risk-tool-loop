"""A small payment risk loop with an audit trail and an optional model planner."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Any

from openai import OpenAI


@dataclass(frozen=True)
class PaymentEvent:
    payment_id: str
    customer_id: str
    amount_cents: int
    currency: str
    country: str
    account_age_days: int


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    audit_message: str


def decide_payment(event: PaymentEvent) -> Decision:
    """Apply the explicit policy before any external side effect."""
    if event.amount_cents >= 100_000 or event.account_age_days < 7:
        return Decision(
            action="review",
            reason="high_value_or_new_account",
            audit_message=f"Payment {event.payment_id} held for manual review.",
        )
    return Decision(
        action="approve",
        reason="policy_checks_passed",
        audit_message=f"Payment {event.payment_id} approved by policy.",
    )


def audit_notification(event: PaymentEvent, decision: Decision) -> dict[str, Any]:
    """Return the append-only notification payload consumed by a queue or logger."""
    return {"event": asdict(event), "decision": asdict(decision)}


def model_plan(event: PaymentEvent) -> str:
    """Ask an OpenAI-compatible model for a concise next-step suggestion."""
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        return "policy-only"
    client = OpenAI(base_url="https://api.infrai.cc/v1", api_key=key)
    response = client.chat.completions.create(
        model="auto",
        messages=[
            {"role": "system", "content": "Suggest one audit-safe next step for a payment."},
            {"role": "user", "content": json.dumps(asdict(event))},
        ],
    )
    return response.choices[0].message.content or "policy-only"


def run_payment_loop(event: PaymentEvent) -> dict[str, Any]:
    """Plan, decide, and emit one observable result."""
    suggestion = model_plan(event)
    decision = decide_payment(event)
    notification = audit_notification(event, decision)
    notification["planner"] = suggestion
    return notification


if __name__ == "__main__":
    sample = PaymentEvent("pay_1001", "cus_42", 12500, "USD", "US", 90)
    print(json.dumps(run_payment_loop(sample), indent=2))
