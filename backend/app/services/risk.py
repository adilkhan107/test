"""Turn raw PPE numbers into a risk score (0 = safe, 100 = severe) and advice."""

LEVELS = [(20, "low"), (45, "medium"), (70, "high"), (101, "critical")]

TYPE_LABELS = {
    "no_hardhat": "workers without a hardhat",
    "no_vest": "workers without a safety vest",
    "no_mask": "workers without a mask",
}

ADVICE = {
    "no_hardhat": "Enforce hardhat use at site entry and stop work for anyone in an active zone without one.",
    "no_vest": "Issue high-visibility vests at the gate and check them during toolbox talks.",
    "no_mask": "Provide masks near dust-producing work and brief the crew on when they are required.",
}


def level_for(score: int) -> str:
    for limit, name in LEVELS:
        if score < limit:
            return name
    return "critical"


def compute_risk(
    compliance: float | None,
    violation_frame_ratio: float,
    peak_violations: int,
) -> tuple[int | None, str]:
    if compliance is None:
        return None, "unknown"
    score = (
        0.60 * (100 - compliance)
        + 0.25 * (violation_frame_ratio * 100)
        + 0.15 * min(100, peak_violations * 25)
    )
    score = max(0, min(100, round(score)))
    return score, level_for(score)


def explain(detections: dict, compliance: float | None, level: str) -> tuple[list[str], list[str]]:
    factors: list[str] = []
    advice: list[str] = []
    if compliance is None:
        return ["No workers were detected, so risk could not be scored."], [
            "Try a clip where workers are clearly visible, or lower CONF_THRESHOLD."
        ]
    factors.append(f"Overall PPE compliance is {compliance:.1f}%.")
    ranked = sorted(TYPE_LABELS, key=lambda k: detections.get(k, 0), reverse=True)
    for key in ranked:
        n = detections.get(key, 0)
        if n:
            factors.append(f"{n} detections of {TYPE_LABELS[key]} across sampled frames.")
            advice.append(ADVICE[key])
    if not advice:
        advice.append("No PPE violations detected. Keep current site controls in place.")
    if level in ("high", "critical"):
        advice.append("Hold a stand-down briefing and re-inspect this area within the day.")
    return factors, advice
