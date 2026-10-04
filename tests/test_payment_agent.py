import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from payment_agent import PaymentEvent, decide_payment, run_payment_loop


def test_new_high_value_payment_is_reviewed_and_audited(monkeypatch):
    monkeypatch.delenv("INFRAI_API_KEY", raising=False)
    event = PaymentEvent("pay_risky", "cus_new", 150_000, "USD", "US", 2)
    decision = decide_payment(event)
    assert decision.action == "review"
    result = run_payment_loop(event)
    assert result["decision"]["reason"] == "high_value_or_new_account"
    assert result["planner"] == "policy-only"
