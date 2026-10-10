"""Model client and template fallback (WBS 5.2, FR-11, FR-16, NFR-05, R06).

generate() returns a draft for one context, written either by Claude or by a fixed template.
The model only words the figures it is given; it never calculates (D-007).

Which writer is used:
- LLM_PROVIDER=template          always the template
- LLM_PROVIDER=anthropic         Claude (falls back to the template on any error)
- LLM_PROVIDER=auto (default)    Claude only if ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN is set
The model is LLM_MODEL (default claude-opus-5-5). No key is ever read from config.yaml.
"""

import json
import os
from dataclasses import dataclass

from src.commentary.context import period_label

DEFAULT_MODEL = "claude-opus-5-5"
TIMEOUT_SECONDS = 20.0

SYSTEM_PROMPT = """You draft month-end cost variance commentary for finance controllers in a \
semiconductor manufacturing group. The data is synthetic.

You receive one flagged item as JSON. Write 2 to 4 sentences, at most 90 words, plain text, \
no headings or lists, in {language}.

Rules for numbers (an automatic check rejects any text that breaks them):
- Use only the numbers in "figures" and in "owner_cause", exactly as given. You may add a \
sign and thousands separators. Never calculate, round, sum, convert or derive any new number.
- Amounts ending in _teur are thousands of EUR: write them as "EUR 477k".
- Do not mention any other number, count or date, except the month and year of the period.

Content:
- Spend items: say how far actual cost was from plan, then separate the volume effect (cost \
that moved with wafer output) from the spend effect (cost above or below the flexed budget).
- Volume items: explain the wafer shortfall or excess and its volume effect on site cost.
- Positive variances are cost above plan (unfavourable).
- If owner_cause is given, use it as the explanation. If it is null, say the cause is not yet \
confirmed by the cost-centre owner. Do not speculate about causes."""


@dataclass
class Draft:
    text: str
    source: str          # "llm" or "template"
    model: str | None
    prompt: dict | None  # what was sent to the model, for the log (NFR-04)
    error: str | None = None


def provider():
    choice = os.environ.get("LLM_PROVIDER", "auto").lower()
    if choice == "auto":
        has_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        return "anthropic" if has_key else "template"
    return choice


def model_name():
    return os.environ.get("LLM_MODEL", DEFAULT_MODEL)


# --- Template --------------------------------------------------------------------------------

def _fmt(value, language, signed=False, decimals=0):
    text = f"{abs(value):,.{decimals}f}"
    if language == "de":
        text = text.replace(",", "_").replace(".", ",").replace("_", ".")
    if signed:
        text = ("+" if value > 0 else "−" if value < 0 else "") + text
    return text


def template_text(context, language="en"):
    f = context["figures"]
    label = period_label(context["period"], language)
    site = context["site"]
    cause = context.get("owner_cause")

    def eur(key, signed=False):
        return f"EUR {_fmt(f[key], language, signed)}k"

    if context["item_type"] == "spend":
        item = f"{context['group_area']} {context['group_account']}"
        pct = _fmt(f["spend_effect_pct_of_flexed_budget"], language, signed=True, decimals=1)
        if language == "de":
            text = (f"{item} bei {site} lag im {label} bei {eur('actual_teur')}, eine Abweichung von "
                    f"{eur('total_variance_teur', True)} zum Plan von {eur('plan_teur')}. "
                    f"Davon entfallen {eur('volume_effect_teur', True)} auf den Mengeneffekt; "
                    f"{eur('spend_effect_teur', True)} ({pct} % des flexiblen Budgets von "
                    f"{eur('flexed_budget_teur')}) sind ein Ausgabeneffekt.")
        else:
            text = (f"{item} at {site} came in at {eur('actual_teur')} in {label}, "
                    f"a variance of {eur('total_variance_teur', True)} against a plan of {eur('plan_teur')}. "
                    f"The volume effect is {eur('volume_effect_teur', True)}; the spend effect is "
                    f"{eur('spend_effect_teur', True)}, or {pct}% of the flexed budget of "
                    f"{eur('flexed_budget_teur')}.")
    else:
        wafers_plan = _fmt(f["plan_wafers"], language)
        wafers_actual = _fmt(f["actual_wafers"], language)
        dev = _fmt(f["wafer_deviation_pct"], language, signed=True, decimals=1)
        if language == "de":
            text = (f"{site} fertigte im {label} {wafers_actual} Wafer gegenüber {wafers_plan} geplanten "
                    f"({dev} %). Der Mengeneffekt auf die Standortkosten beträgt "
                    f"{eur('site_volume_effect_teur', True)}, der Ausgabeneffekt "
                    f"{eur('site_spend_effect_teur', True)}. Kosten je Wafer: EUR "
                    f"{_fmt(f['cost_per_wafer_actual_eur'], language)} (Plan: EUR "
                    f"{_fmt(f['cost_per_wafer_plan_eur'], language)}).")
        else:
            text = (f"{site} produced {wafers_actual} wafers in {label} against a plan of {wafers_plan} "
                    f"({dev}%). The volume effect on site cost is {eur('site_volume_effect_teur', True)} "
                    f"and the spend effect is {eur('site_spend_effect_teur', True)}. Cost per wafer was "
                    f"EUR {_fmt(f['cost_per_wafer_actual_eur'], language)} against a plan of "
                    f"EUR {_fmt(f['cost_per_wafer_plan_eur'], language)}.")

    if language == "de":
        text += f" Ursache laut Kostenstellenverantwortlichem: {cause}" if cause else \
            " Die Ursache ist vom Kostenstellenverantwortlichen noch nicht bestätigt."
    else:
        text += f" Cause given by the cost-centre owner: {cause}" if cause else \
            " The cause is not yet confirmed by the cost-centre owner."
    return text


# --- Claude ----------------------------------------------------------------------------------

def build_prompt(context, language="en", feedback=None):
    payload = {k: v for k, v in context.items() if k != "item_id"}
    payload["period_label"] = period_label(context["period"], language)
    user = json.dumps(payload, ensure_ascii=False, indent=2)
    if feedback:
        user += f"\n\nYour previous draft was rejected: {feedback} Rewrite it using only the given numbers."
    return {
        "system": SYSTEM_PROMPT.format(language="German" if language == "de" else "English"),
        "user": user,
    }


def _call_model(prompt):
    """Send one prompt to Claude and return the text. Raises on any failure."""
    import anthropic

    client = anthropic.Anthropic(timeout=TIMEOUT_SECONDS, max_retries=0)
    response = client.beta.messages.create(
        model=model_name(),
        max_tokens=4000,
        system=prompt["system"],
        messages=[{"role": "user", "content": prompt["user"]}],
        output_config={"effort": "low"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("The model declined the request")
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    if not text:
        raise RuntimeError(f"Empty answer (stop reason {response.stop_reason})")
    return text


def generate(context, language="en", feedback=None):
    """One draft for the context. Falls back to the template if the model is off or fails."""
    if provider() != "anthropic":
        return Draft(template_text(context, language), "template", None, None)

    prompt = build_prompt(context, language, feedback)
    try:
        import anthropic
        try:
            return Draft(_call_model(prompt), "llm", model_name(), prompt)
        except anthropic.APITimeoutError:
            error = f"Timeout after {TIMEOUT_SECONDS:.0f} s"
        except anthropic.APIConnectionError:
            error = "Network error"
        except anthropic.RateLimitError:
            error = "Rate limited"
        except anthropic.APIStatusError as exc:
            error = f"API error {exc.status_code}"
        except anthropic.AnthropicError as exc:  # e.g. no credentials
            error = f"Client error: {exc}"
    except (ImportError, RuntimeError) as exc:
        error = str(exc)
    return Draft(template_text(context, language), "template", None, prompt, error=error)
