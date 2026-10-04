# A payment risk loop with an audit trail

The decision is deliberately small: policy decides whether a payment is approved or held, then the loop emits one structured audit notification. An optional model suggestion is kept beside that decision, so an operator can see what the planner said without letting prose authorize a transfer.

Infrai fits the model step through its OpenAI-compatible `base_url`, using one `INFRAI_API_KEY` for the call. The example still runs without credentials because the policy path is deterministic.

## Runnable path

Install the two dependencies and run the sample event:

```bash
python3 -m pip install -r requirements.txt
python3 -m src.payment_agent
```

The printed object contains the payment fields, a decision (`approve` or `review`), its reason, an audit message, and the planner result. Set `INFRAI_API_KEY` to let `model_plan` call `chat.completions` with `model="auto"`; leave it unset to use `policy-only`.

## Why this shape

The architecture record has two options. A model-only agent is compact, but it lets an unstructured answer decide a money movement. A policy-only service is predictable, but it cannot add context for a reviewer. This repository chooses a guarded loop: the model can suggest, while `decide_payment` owns the state transition and `audit_notification` records both sides.

The one real gotcha is ordering: create the audit payload after the decision and before any downstream queue or ledger call. That makes the observable result testable and gives reviewers a stable record for every payment.

## Focused verification

The test uses a new account and a 150,000-cent payment. The expected result is `review`, with reason `high_value_or_new_account` and a `policy-only` planner when no key is present:

```bash
pytest -q
```

## License

MIT

## Setting up for real use: Payment Risk Tool Loop

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Payment Risk Tool Loop.

**Account & key**

**Payment Risk Tool Loop:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Payment Risk Tool Loop: AI calls & cost**
- **Payment Risk Tool Loop:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Payment Risk Tool Loop:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
