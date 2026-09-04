#!/usr/bin/env python3
"""
Standardized Mean Difference (Cohen's d, Hedges' g, Glass's Delta)
Computes Cohen's d with small-sample Hedges' g correction and unequal-variance Glass's delta with standard errors.

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import math
import os
from typing import Dict, Any, List, Optional


def cohens_d(mean1: float, mean2: float, std1: float, std2: float, n1: int = 1, n2: int = 1) -> float:
    """
    Compute Cohen's d: (mean1 - mean2) / pooled_standard_deviation.

    Uses pooled standard deviation assuming equal or unequal sample sizes.
    For n1=n2=1, falls back to using the average of std1 and std2 as denominator.
    """
    if n1 < 1 or n2 < 1:
        raise ValueError("Sample sizes must be at least 1.")
    if std1 < 0 or std2 < 0:
        raise ValueError("Standard deviations must be non-negative.")
    denominator = n1 + n2 - 2
    if denominator <= 0:
        # Not enough degrees of freedom for pooled SD; use average SD as fallback
        pooled_std = (std1 + std2) / 2.0
    else:
        pooled_std = math.sqrt(((n1 - 1) * std1 ** 2 + (n2 - 1) * std2 ** 2) / denominator)
    if pooled_std == 0:
        return 0.0
    return (mean1 - mean2) / pooled_std


def hedges_g(mean1: float, mean2: float, std1: float, std2: float, n1: int = 1, n2: int = 1) -> float:
    """
    Compute Hedges' g: Cohen's d with small-sample bias correction.

    The correction factor J(df) = 1 - 3 / (4 * df - 1) where df = n1 + n2 - 2.
    """
    d = cohens_d(mean1, mean2, std1, std2, n1, n2)
    df = n1 + n2 - 2
    if df <= 0:
        return d
    j = 1.0 - (3.0 / (4.0 * df - 1.0))
    return d * j


def glasses_delta(mean1: float, mean2: float, std_control: float) -> float:
    """
    Compute Glass's Delta: (mean1 - mean2) / control_group_std.

    Uses the control group standard deviation (unequal-variance approach).
    """
    if std_control <= 0:
        raise ValueError("Control group standard deviation must be positive.")
    return (mean1 - mean2) / std_control


def standard_error_effect_size(d: float, n1: int, n2: int) -> float:
    """
    Compute the standard error of the effect size (Cohen's d / Hedges' g).

    SE = sqrt((n1 + n2) / (n1 * n2) + d^2 / (2 * (n1 + n2)))
    """
    if n1 < 1 or n2 < 1:
        raise ValueError("Sample sizes must be at least 1.")
    if n1 + n2 == 0:
        return float("inf")
    return math.sqrt((n1 + n2) / (n1 * n2) + d ** 2 / (2 * (n1 + n2)))


def calculate_metrics(**kwargs) -> Dict[str, Any]:
    """
    Core domain algorithm for effect-size-hedges-g-glass-delta.

    Computes Cohen's d, Hedges' g, and Glass's delta from input parameters.

    Expected keyword arguments:
        mean1, mean2: group means
        std1, std2: group standard deviations
        n1, n2: sample sizes (default 1)
    Falls back to legacy behavior if statistical params are not provided.
    """
    params: Dict[str, Any] = {}
    for k, v in kwargs.items():
        if v is not None:
            try:
                params[k] = float(v)
            except (ValueError, TypeError):
                params[k] = str(v)

    # Check if we have statistical parameters for proper effect size computation
    has_stats = all(k in params for k in ("mean1", "mean2", "std1", "std2"))

    if has_stats:
        mean1 = float(params["mean1"])
        mean2 = float(params["mean2"])
        std1 = float(params["std1"])
        std2 = float(params["std2"])
        n1 = int(params.get("n1", 1))
        n2 = int(params.get("n2", 1))

        if n1 < 1:
            n1 = 1
        if n2 < 1:
            n2 = 1

        d = cohens_d(mean1, mean2, std1, std2, n1, n2)
        g = hedges_g(mean1, mean2, std1, std2, n1, n2)
        delta = glasses_delta(mean1, mean2, std2)
        se = standard_error_effect_size(d, n1, n2)

        score = round(g, 4)
        result = {
            "tool": "effect-size-hedges-g-glass-delta",
            "cohens_d": round(d, 4),
            "hedges_g": round(g, 4),
            "glasses_delta": round(delta, 4),
            "standard_error": round(se, 4),
            "n1": n1,
            "n2": n2,
            "score": score,
            "classification": _classify_effect(g),
            "clinical_recommendation": _clinical_recommendation(g),
            "inputs_evaluated": len(params),
        }
    else:
        # Legacy fallback: deterministic weighted sum for backwards compatibility
        numeric_vals = [val for val in params.values() if isinstance(val, (int, float))]
        primary_val = numeric_vals[0] if numeric_vals else 1.0

        score = primary_val
        for idx, nv in enumerate(numeric_vals[1:], start=2):
            score += nv * (1.0 / idx)

        rounded_score = round(score, 2)
        result = {
            "tool": "effect-size-hedges-g-glass-delta",
            "score": rounded_score,
            "classification": _classify_score(rounded_score),
            "clinical_recommendation": _clinical_recommendation_legacy(rounded_score),
            "inputs_evaluated": len(params),
            "note": "Legacy mode: provide mean1, mean2, std1, std2 for statistical effect sizes.",
        }

    return result


def _classify_effect(g: float) -> str:
    """Classify Hedges' g effect size magnitude."""
    abs_g = abs(g)
    if abs_g < 0.2:
        return "Negligible"
    elif abs_g < 0.5:
        return "Small"
    elif abs_g < 0.8:
        return "Medium"
    else:
        return "Large"


def _clinical_recommendation(g: float) -> str:
    """Map effect size to clinical recommendation."""
    abs_g = abs(g)
    if abs_g < 0.2:
        return "Negligible effect — no clinically meaningful difference detected."
    elif abs_g < 0.5:
        return "Small effect — monitor and consider secondary evaluation."
    elif abs_g < 0.8:
        return "Medium effect — close observation recommended."
    else:
        return "Large effect — clinically significant difference; consider intervention."


def _classify_score(score: float) -> str:
    """Legacy classification based on raw score."""
    if score < 10.0:
        return "Low / Standard"
    elif score < 25.0:
        return "Moderate / Intermediate"
    else:
        return "High / Severe"


def _clinical_recommendation_legacy(score: float) -> str:
    """Legacy clinical recommendation based on raw score."""
    if score < 10.0:
        return "Standard monitoring or negative cutoff"
    elif score < 25.0:
        return "Close observation or secondary evaluation"
    else:
        return "Urgent clinical intervention or primary positive finding"


def process_single(args) -> None:
    kwargs = vars(args)
    kwargs.pop("func", None)
    res = calculate_metrics(**kwargs)
    print(json.dumps(res, indent=2))


def process_batch(input_csv: str, output_csv: str) -> None:
    import os
    if not os.path.isfile(input_csv):
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_fields = fieldnames + ["score", "classification", "clinical_recommendation"]
    out_rows = []

    for r in rows:
        calc_res = calculate_metrics(**r)
        row_dict = dict(r)
        row_dict["score"] = calc_res["score"]
        row_dict["classification"] = calc_res["classification"]
        row_dict["clinical_recommendation"] = calc_res["clinical_recommendation"]
        out_rows.append(row_dict)

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Processed {len(out_rows)} records -> {output_csv}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Standardized Mean Difference (Cohen's d, Hedges' g, Glass's Delta)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single parser
    single_parser = subparsers.add_parser("single", help="Evaluate single case")
    single_parser.add_argument("--mean1", type=float, default=10.0, help="Group 1 mean")
    single_parser.add_argument("--mean2", type=float, default=5.0, help="Group 2 mean")
    single_parser.add_argument("--std1", type=float, default=2.0, help="Group 1 standard deviation")
    single_parser.add_argument("--std2", type=float, default=2.0, help="Group 2 standard deviation")
    single_parser.add_argument("--n1", type=int, default=30, help="Group 1 sample size")
    single_parser.add_argument("--n2", type=int, default=30, help="Group 2 sample size")
    single_parser.add_argument("--v1", type=float, help="(Legacy) Primary parameter")
    single_parser.add_argument("--v2", type=float, help="(Legacy) Secondary parameter")
    single_parser.add_argument("--v3", type=float, help="(Legacy) Tertiary parameter")
    single_parser.set_defaults(func=process_single)

    # Batch parser
    batch_parser = subparsers.add_parser("batch", help="Process batch CSV")
    batch_parser.add_argument("-i", "--input", required=True, help="Input CSV")
    batch_parser.add_argument("-o", "--output", default="results.csv", help="Output CSV")

    args = parser.parse_args(argv)

    if args.command == "single":
        args.func(args)
    elif args.command == "batch":
        process_batch(args.input, args.output)


if __name__ == "__main__":
    main()
