from bench.metrics import Trial, summarize


def test_empty_benchmark_does_not_report_fake_metrics():
    result = summarize([])
    assert result["repositories"] == 0
    assert result["test_pass_rate"] is None


def test_summary_counts_trials():
    trials = [Trial("a", "rules_only", True, True, 0, 0.0, 10.0, 4)]
    assert summarize(trials)["test_pass_rate"] == 1.0
