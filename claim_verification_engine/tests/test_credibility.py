from app.services.source_credibility import SourceCredibilityAnalyzer
from app.services.bayesian_verifier import BayesianVerifier


def test_domain_pattern_requires_hostname_boundary():
    score = SourceCredibilityAnalyzer().calculate_credibility_score
    assert score('https://pib.gov.in/path') == 0.95
    assert score('subdomain.gov.in') == 0.9
    assert score('https://attacker.com/path/gov.in') == 0.55
    assert score('gov.in.attacker.com') == 0.55
    assert score('fakegov.in') != 0.9


def test_no_evidence_has_no_invented_precision():
    assert BayesianVerifier().bayesian_update([]) == (0.5, (0.0, 1.0))


def test_unknown_graph_nodes_do_not_crash():
    result = SourceCredibilityAnalyzer().detect_coordinated_behavior(['unknown.example', 'other.example'])
    assert 0 <= result['average_credibility'] <= 1
