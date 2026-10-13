import pytest
from effect_sizes import (
    calculate_metrics,
    cohens_d,
    hedges_g,
    glasses_delta,
    standard_error_effect_size,
    process_batch,
)


def test_effect_sizes_single():
    res = calculate_metrics(v1=12.0, v2=4.0)
    assert "score" in res
    assert "classification" in res
    assert res["score"] > 0


def test_effect_sizes_batch(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient,v1,v2\nPat_001,15.0,3.0\nPat_002,5.0,1.0\n", encoding="utf-8")

    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "Pat_001" in content
    assert "score" in content


# --- Statistical calculation tests ---

def test_cohens_d_basic():
    # mean1=10, mean2=8, std1=2, std2=2, n1=n2=30
    # pooled_std = sqrt(((29*4) + (29*4)) / 58) = sqrt(232/58) = sqrt(4) = 2.0
    # d = (10-8)/2 = 1.0
    d = cohens_d(10.0, 8.0, 2.0, 2.0, 30, 30)
    assert abs(d - 1.0) < 1e-6


def test_cohens_d_zero_difference():
    d = cohens_d(5.0, 5.0, 1.0, 1.0, 10, 10)
    assert abs(d - 0.0) < 1e-6


def test_cohens_d_negative_effect():
    d = cohens_d(8.0, 10.0, 2.0, 2.0, 30, 30)
    assert abs(d - (-1.0)) < 1e-6


def test_hedges_g_correction():
    # Hedges' g should be slightly smaller than Cohen's d for small samples
    d = cohens_d(10.0, 8.0, 2.0, 2.0, 10, 10)
    g = hedges_g(10.0, 8.0, 2.0, 2.0, 10, 10)
    assert abs(g) < abs(d)
    assert g != 0


def test_hedges_g_large_sample():
    # For large samples, g should be very close to d
    d = cohens_d(10.0, 8.0, 2.0, 2.0, 1000, 1000)
    g = hedges_g(10.0, 8.0, 2.0, 2.0, 1000, 1000)
    assert abs(g - d) < 0.001


def test_glasses_delta_basic():
    # mean1=10, mean2=8, std_control=2
    # delta = (10-8)/2 = 1.0
    delta = glasses_delta(10.0, 8.0, 2.0)
    assert abs(delta - 1.0) < 1e-6


def test_glasses_delta_invalid_std():
    with pytest.raises(ValueError):
        glasses_delta(10.0, 8.0, 0.0)


def test_standard_error_positive():
    se = standard_error_effect_size(1.0, 30, 30)
    assert se > 0


def test_calculate_metrics_statistical():
    res = calculate_metrics(mean1=10.0, mean2=8.0, std1=2.0, std2=2.0, n1=30, n2=30)
    assert "cohens_d" in res
    assert "hedges_g" in res
    assert "glasses_delta" in res
    assert "standard_error" in res
    assert abs(res["cohens_d"] - 1.0) < 1e-6
    assert res["classification"] in ("Negligible", "Small", "Medium", "Large")


def test_calculate_metrics_classification_large():
    res = calculate_metrics(mean1=20.0, mean2=10.0, std1=2.0, std2=2.0, n1=50, n2=50)
    assert res["classification"] == "Large"


def test_calculate_metrics_classification_negligible():
    res = calculate_metrics(mean1=10.1, mean2=10.0, std1=5.0, std2=5.0, n1=30, n2=30)
    assert res["classification"] == "Negligible"


def test_calculate_metrics_invalid_sample_size():
    with pytest.raises(ValueError, match="at least 2"):
        calculate_metrics(mean1=10.0, mean2=8.0, std1=2.0, std2=2.0, n1=0, n2=0)


def test_process_batch_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        process_batch(str(tmp_path / "nonexistent.csv"), str(tmp_path / "out.csv"))


@pytest.mark.parametrize("n1,n2", [(1, 10), (10, 1), (2.5, 9), (-1, 3)])
def test_invalid_group_sizes(n1, n2):
    with pytest.raises(ValueError):
        calculate_metrics(mean1=10, mean2=8, std1=2, std2=2, n1=n1, n2=n2)


@pytest.mark.parametrize("std1,std2", [(0, 0), (-1, 2), (float("nan"), 2),
                                         (float("inf"), 2)])
def test_undefined_or_invalid_variance(std1, std2):
    with pytest.raises(ValueError):
        calculate_metrics(mean1=10, mean2=8, std1=std1, std2=std2, n1=30, n2=30)


def test_partial_statistics_are_not_treated_as_legacy():
    with pytest.raises(ValueError, match="requires"):
        calculate_metrics(mean1=10, mean2=8, std1=2)


def test_correct_unbalanced_pooled_sd():
    import math
    d = cohens_d(12, 8, 2, 4, 10, 30)
    expected = 4 / math.sqrt((9 * 4 + 29 * 16) / 38)
    assert d == pytest.approx(expected)


def test_nonfinite_data_rejected():
    with pytest.raises(ValueError):
        standard_error_effect_size(float("nan"), 30, 30)
    with pytest.raises(ValueError):
        glasses_delta(1, 2, float("inf"))


def test_batch_statistical_columns_and_values(tmp_path):
    import csv
    src = tmp_path / "stats.csv"
    out = tmp_path / "results.csv"
    src.write_text("mean1,mean2,std1,std2,n1,n2\n10,8,2,2,30,30\n", encoding="utf-8")
    process_batch(str(src), str(out))
    with out.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert float(rows[0]["cohens_d"]) == pytest.approx(1)
    assert float(rows[0]["hedges_g"]) < 1
    assert float(rows[0]["glasses_delta"]) == pytest.approx(1)
    assert float(rows[0]["standard_error"]) > 0


def test_batch_invalid_row_reports_line_without_writing(tmp_path):
    src = tmp_path / "stats.csv"
    out = tmp_path / "results.csv"
    src.write_text("mean1,mean2,std1,std2,n1,n2\n10,8,0,0,30,30\n", encoding="utf-8")
    with pytest.raises(ValueError, match="row 2"):
        process_batch(str(src), str(out))
    assert not out.exists()


def test_legacy_mode_has_no_clinical_claim():
    result = calculate_metrics(v1=12, v2=4)
    assert "not a statistical effect size" in result["clinical_recommendation"]
