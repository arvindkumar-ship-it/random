import numpy as np
from scipy import stats
from datetime import datetime
import math
from typing import List, Dict, Any, Tuple


class BayesianVerifier:
    def __init__(self, prior_prob: float = 0.5, lambda_decay: float = 0.1):
        self.prior = prior_prob
        self.lambda_decay = lambda_decay
        self.weights = {
            'credibility': 0.4,
            'recency': 0.2,
            'relevance': 0.25,
            'consistency': 0.15
        }

    def calculate_recency_score(self, evidence_date: datetime) -> float:
        """Exponential decay for recency"""
        delta_days = (datetime.now() - evidence_date).days
        return math.exp(-self.lambda_decay * max(0, delta_days))

    def calculate_cosine_similarity(self, claim_embedding: np.ndarray,
                                     evidence_embedding: np.ndarray) -> float:
        """Semantic relevance using cosine similarity"""
        norm_claim = np.linalg.norm(claim_embedding)
        norm_evidence = np.linalg.norm(evidence_embedding)
        if norm_claim == 0 or norm_evidence == 0:
            return 0.0
        return float(np.dot(claim_embedding, evidence_embedding) /
                      (norm_claim * norm_evidence))

    def calculate_jaccard_consistency(self, claim_entities: set,
                                       evidence_entities: set) -> float:
        """Entity overlap between claim and evidence"""
        if not claim_entities or not evidence_entities:
            return 0.0
        intersection = len(claim_entities.intersection(evidence_entities))
        union = len(claim_entities.union(evidence_entities))
        return intersection / union if union > 0 else 0.0

    def calculate_evidence_quality_score(self, evidence: Dict[str, Any]) -> float:
        """Calculate Evidence Quality Score (EQS)"""
        recency = self.calculate_recency_score(evidence['publication_date'])
        eqs = (
            self.weights['credibility'] * evidence['credibility_score'] +
            self.weights['recency'] * recency +
            self.weights['relevance'] * evidence['relevance_score'] +
            self.weights['consistency'] * evidence['entity_overlap']
        )
        return min(max(eqs, 0.0), 1.0)

    def bayesian_update(self, evidence_list: List[Dict[str, Any]]) -> Tuple[float, Tuple[float, float]]:
        """
        Bayesian belief update
        Returns: (heuristic_score, uninformative_interval). No calibration dataset exists.
        """
        if not evidence_list:
            return 0.5, (0.0, 1.0)

        # Calculate likelihood for each evidence
        likelihoods = []
        for evidence in evidence_list:
            eqs = self.calculate_evidence_quality_score(evidence)
            likelihood = eqs if evidence['supports_claim'] else (1 - eqs)
            likelihoods.append(max(0.01, min(0.99, likelihood)))

        # Combine likelihoods (geometric mean for robustness)
        combined_likelihood = stats.gmean(likelihoods) if likelihoods else 0.5

        # Bayesian update
        numerator = combined_likelihood * self.prior
        denominator = (combined_likelihood * self.prior +
                        (1 - combined_likelihood) * (1 - self.prior))
        posterior = numerator / denominator if denominator > 0 else 0.5

        # A fixed invented concentration cannot establish a 95% interval.
        return float(posterior), (0.0, 1.0)
