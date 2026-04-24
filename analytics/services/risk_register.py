"""Risk reyestri — har bir risk uchun (ehtimollik × ta'sir) balli."""
from typing import Any


def score_risk_register(risks: list[dict[str, Any]]) -> dict[str, Any]:
    """Kirish: [{"name": ..., "probability": 0..1, "impact": 0..1}, ...].

    Yig'ma ball — barcha p*i ning yig'indisi. Aslida bu darajalanadigan emas,
    lekin proyekt darajasida nisbiy taqqoslash uchun yetarli.
    """
    if not risks:
        raise ValueError("Kamida bitta risk kiriting")

    scored: list[dict[str, Any]] = []
    total = 0.0

    for r in risks:
        p = float(r["probability"])
        i = float(r["impact"])
        if not (0 <= p <= 1) or not (0 <= i <= 1):
            raise ValueError("Ehtimollik va ta'sir 0..1 oralig'ida")

        score = p * i
        total += score
        scored.append({
            "name": str(r.get("name", "")),
            "probability": p,
            "impact": i,
            "score": score,
        })

    max_single = max(item["score"] for item in scored)

    return {
        "risks": scored,
        "aggregate_score": float(total),
        "max_risk_score": float(max_single),
        "risk_count": len(scored),
    }
