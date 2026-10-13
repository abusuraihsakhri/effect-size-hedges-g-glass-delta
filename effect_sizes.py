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


def _validate_samples(n1: int, n2: int) -> None:
    """Require independently estimable sample standard deviations."""
    if any(isinstance(n, bool) or not isinstance(n, int) or n < 2 for n in (n1, n2)):
        raise ValueError("Both sample sizes must be integers of at least 2.")


def _finite_number(value: float, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite number.") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number.")
    return result


def cohens_d(mean1: float, mean2: float, std1: float, std2: float, n1: int = 1, n2: int = 1) -> float:
    """Independent-group Cohen's d, using the sample-size-weighted pooled SD.

    Requires at least two observations per group. The pooled variance must
    be strictly positive; d is undefined when both within-group SDs are zero.
    """
    _validate_samples(n1, n2)
    mean1 = _finite_number(mean1, "mean1")
    mean2 = _finite_number(mean2, "mean2")
    std1 = _finite_number(std1, "std1")
    std2 = _finite_number(std2, "std2")
    if std1 < 0 or std2 < 0:
        raise ValueError("Standard deviations must be non-negative.")
    df = n1 + n2 - 2
    # hypot avoids premature overflow in the sum of squared deviations.
    pooled_std = math.hypot(math.sqrt(n1 - 1) * std1, math.sqrt(n2 - 1) * std2) / math.sqrt(df)
    if pooled_std <= 0 or not math.isfinite(pooled_std):
        raise ValueError("Pooled standard deviation must be finite and positive.")
    d = (mean1 - mean2) / pooled_std
    if not math.isfinite(d):
        raise ValueError("Computed effect size is not finite.")
    return d


def hedges_g(mean1: float, mean2: float, std1: float, std2: float, n1: int = 1, n2: int = 1) -> float:
    """Hedges' g with the usual approximate small-sample correction.

    J(df) ≈ 1 - 3 / (4*df - 1), where df=n1+n2-2.
    """
    d = cohens_d(mean1, mean2, std1, std2, n1, n2)
    df = n1 + n2 - 2
    return d * (1.0 - 3.0 / (4.0 * df - 1.0))


def glasses_delta(mean1: float, mean2: float, std_control: float) -> float:
    """Glass's delta, standardized by group 2's (control) sample SD."""
    mean1 = _finite_number(mean1, "mean1")
    mean2 = _finite_number(mean2, "mean2")
    std_control = _finite_number(std_control, "std_control")
    if std_control <= 0:
        raise ValueError("Control group standard deviation must be positive.")
    delta = (mean1 - mean2) / std_control
    if not math.isfinite(delta):
        raise ValueError("Computed Glass's delta is not finite.")
    return delta


def standard_error_effect_size(d: float, n1: int, n2: int) -> float:
    """Approximate large-sample standard error of Cohen's d.

    This is not the exact SE of Hedges' g or Glass's delta.
    """
    _validate_samples(n1, n2)
    d = _finite_number(d, "d")
    variance = 1.0 / n1 + 1.0 / n2 + d ** 2 / (2.0 * (n1 + n2))
    if not math.isfinite(variance):
        raise ValueError("Computed effect-size variance is not finite.")
    return math.sqrt(variance)


def calculate_metrics(**kwargs) -> Dict[str, Any]:
    """Compute independent-group standardized mean differences.

    Statistical mode requires mean1, mean2, std1, std2, n1, and n2.
    Group 2 is the control group for Glass's delta. The legacy v1/v2
    scoring behavior is retained solely for compatibility, not inference.
    """
    params = {k: v for k, v in kwargs.items() if v is not None and k not in ("func", "command")}
    required_stats = ("mean1", "mean2", "std1", "std2")
    if any(k in params for k in required_stats):
        missing = [k for k in (*required_stats, "n1", "n2") if k not in params or params[k] == ""]
        if missing:
            raise ValueError("Statistical mode requires: " + ", ".join(missing))
        def sample_size(key: str) -> int:
            value = _finite_number(params[key], key)
            if not value.is_integer() or value < 2:
                raise ValueError(f"{key} must be an integer of at least 2.")
            return int(value)

        n1, n2 = sample_size("n1"), sample_size("n2")
        mean1, mean2, std1, std2 = (_finite_number(params[k], k) for k in required_stats)
        d = cohens_d(mean1, mean2, std1, std2, n1, n2)
        g = hedges_g(mean1, mean2, std1, std2, n1, n2)
        delta = glasses_delta(mean1, mean2, std2)
        se = standard_error_effect_size(d, n1, n2)
        score = round(g, 4)
        return {
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

    # Historical, non-statistical scoring scheme. Not an effect-size estimate.
    numeric_vals = []
    for value in params.values():
        try:
            numeric_vals.append(_finite_number(value, "legacy input"))
        except ValueError:
            continue
    score = numeric_vals[0] if numeric_vals else 1.0
    for i, value in enumerate(numeric_vals[1:], start=2):
        score += value / i
    if not math.isfinite(score):
        raise ValueError("Legacy score is not finite.")
    score = round(score, 2)
    return {
        "tool": "effect-size-hedges-g-glass-delta",
        "score": score,
        "classification": _classify_score(score),
        "clinical_recommendation": _clinical_recommendation_legacy(score),
        "inputs_evaluated": len(params),
        "note": "Legacy mode is not a validated effect size; supply all six statistical inputs.",
    }


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
    """Magnitude alone does not justify clinical treatment recommendations."""
    return "Effect-size magnitude is descriptive; assess uncertainty and clinical context."


def _classify_score(score: float) -> str:
    """Legacy classification based on raw score."""
    if score < 10.0:
        return "Low / Standard"
    elif score < 25.0:
        return "Moderate / Intermediate"
    else:
        return "High / Severe"


def _clinical_recommendation_legacy(score: float) -> str:
    """The retained legacy score has no validated clinical interpretation."""
    return "Legacy score is not a statistical effect size or clinical decision rule."


def process_single(args) -> None:
    kwargs = vars(args)
    kwargs.pop("func", None)
    res = calculate_metrics(**kwargs)
    print(json.dumps(res, indent=2))


def process_batch(input_csv: str, output_csv: str) -> None:
    """Evaluate each CSV row and preserve source columns in the output."""
    if not os.path.isfile(input_csv):
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    with open(input_csv, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames or len(fieldnames) != len(set(fieldnames)):
            raise ValueError("CSV requires a header row with unique column names.")
        rows = list(reader)

    metric_fields = ("cohens_d", "hedges_g", "glasses_delta", "standard_error",
                     "score", "classification", "clinical_recommendation")
    out_fields = list(dict.fromkeys([*fieldnames, *metric_fields]))
    results = []
    for row_number, row in enumerate(rows, start=2):
        try:
            if None in row:
                raise ValueError("CSV row has more columns than the header.")
            result = calculate_metrics(**row)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid CSV row {row_number}: {exc}") from exc
        results.append({**row, **{k: result[k] for k in metric_fields if k in result}})

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(results)
    print(f"Processed {len(results)} records -> {output_csv}")


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
