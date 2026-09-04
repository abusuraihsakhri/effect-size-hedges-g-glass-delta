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
    # Should handle n < 1 gracefully
    res = calculate_metrics(mean1=10.0, mean2=8.0, std1=2.0, std2=2.0, n1=0, n2=0)
    assert "score" in res


def test_process_batch_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        process_batch(str(tmp_path / "nonexistent.csv"), str(tmp_path / "out.csv"))
