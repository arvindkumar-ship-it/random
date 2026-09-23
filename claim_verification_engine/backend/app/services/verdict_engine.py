from typing import List, Dict, Any, Optional
from .bayesian_verifier import BayesianVerifier


class DempsterShaferFusion:
    """
    Combine evidence from multiple sources with uncertainty.
    Better than simple averaging when sources conflict.
    """

    def __init__(self):
        self.hypotheses = ['TRUE', 'FALSE', 'UNCERTAIN']

    def calculate_mass_function(self, evidence_list: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate basic probability assignment (mass function) for each hypothesis.
        """
        mass = {'TRUE': 0.0, 'FALSE': 0.0, 'UNCERTAIN': 0.0}

        for evidence in evidence_list:
            credibility = evidence['credibility_score'] * evidence['relevance_score']
            weight = evidence['recency_score'] * evidence['entity_overlap']

            if evidence['supports_claim']:
                mass['TRUE'] += credibility * weight
                mass['UNCERTAIN'] += (1 - credibility) * weight
            else:
                mass['FALSE'] += credibility * weight
                mass['UNCERTAIN'] += (1 - credibility) * weight

        total = sum(mass.values())
        if total > 0:
            mass = {k: v / total for k, v in mass.items()}
        else:
            mass = {'TRUE': 0.0, 'FALSE': 0.0, 'UNCERTAIN': 1.0}

        return mass

    def combine_mass_functions(self, mass1: Dict[str, float],
                                mass2: Dict[str, float]) -> Dict[str, float]:
        """Dempster's rule of combination"""
        combined = {'TRUE': 0.0, 'FALSE': 0.0, 'UNCERTAIN': 0.0}
        conflict = 0.0

        for h1 in self.hypotheses:
            for h2 in self.hypotheses:
                intersection = self._hypothesis_intersection(h1, h2)
                if intersection:
                    combined[intersection] += mass1[h1] * mass2[h2]
                else:
                    conflict += mass1[h1] * mass2[h2]

        if conflict < 1.0:
            combined = {k: v / (1 - conflict) for k, v in combined.items()}

        return combined

    def _hypothesis_intersection(self, h1: str, h2: str) -> Optional[str]:
        """Define intersection of hypotheses"""
        if h1 == h2:
            return h1
        if h1 == 'UNCERTAIN' or h2 == 'UNCERTAIN':
            return h2 if h1 == 'UNCERTAIN' else h1
        return None  # TRUE and FALSE are mutually exclusive

    def calculate_belief_plausibility(self, mass: Dict[str, float]) -> Dict[str, Any]:
        """
        Belief: minimum probability that hypothesis is true
        Plausibility: maximum probability that hypothesis could be true
        """
        belief = mass.copy()
        plausibility = {
            'TRUE': mass['TRUE'] + mass['UNCERTAIN'],
            'FALSE': mass['FALSE'] + mass['UNCERTAIN'],
            'UNCERTAIN': 1.0
        }

        return {
            'belief': belief,
            'plausibility': plausibility,
            'belief_interval': {
                'TRUE': (belief['TRUE'], plausibility['TRUE']),
                'FALSE': (belief['FALSE'], plausibility['FALSE'])
            }
        }


class FinalVerdictEngine:
    def __init__(self, supported_threshold: float = 0.75, refuted_threshold: float = 0.25):
        self.bayesian_verifier = BayesianVerifier()
        self.ds_fusion = DempsterShaferFusion()
        self.supported_threshold = supported_threshold
        self.refuted_threshold = refuted_threshold

    def generate_verdict(self, claim: str, evidence_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Method 1: Bayesian
        posterior, ci = self.bayesian_verifier.bayesian_update(evidence_list)

        # Method 2: Dempster-Shafer
        mass = self.ds_fusion.calculate_mass_function(evidence_list)
        belief_plaus = self.ds_fusion.calculate_belief_plausibility(mass)

        # Method 3: Weighted voting
        weighted_votes = {
            'TRUE': sum(e['credibility_score'] * e['relevance_score'] * e['recency_score']
                        for e in evidence_list if e['supports_claim']),
            'FALSE': sum(e['credibility_score'] * e['relevance_score'] * e['recency_score']
                         for e in evidence_list if not e['supports_claim'])
        }
        total_votes = weighted_votes['TRUE'] + weighted_votes['FALSE']
        vote_score = weighted_votes['TRUE'] / total_votes if total_votes > 0 else 0.5

        # Ensemble decision
        ensemble_score = (
            0.4 * posterior +
            0.35 * belief_plaus['belief']['TRUE'] +
            0.25 * vote_score
        )

        # Determine verdict
        if not evidence_list:
            verdict = "UNVERIFIABLE"
        elif ensemble_score >= self.supported_threshold:
            verdict = "SUPPORTED"
        elif ensemble_score <= self.refuted_threshold:
            verdict = "REFUTED"
        elif ensemble_score >= 0.45:
            verdict = "MIXED"
        else:
            verdict = "UNVERIFIABLE"

        reasoning = self._generate_reasoning(claim, evidence_list, verdict, ensemble_score)

        return {
            'claim': claim,
            'verdict': verdict,
            'confidence': ensemble_score,
            'confidence_interval_95': ci,
            'method_scores': {
                'bayesian': posterior,
                'dempster_shafer': belief_plaus['belief']['TRUE'],
                'weighted_vote': vote_score
            },
            'belief_interval': belief_plaus['belief_interval'],
            'reasoning': reasoning,
            'evidence_count': len(evidence_list),
            'supporting_count': sum(1 for e in evidence_list if e['supports_claim']),
            'contradicting_count': sum(1 for e in evidence_list if not e['supports_claim'])
        }

    def _generate_reasoning(self, claim: str, evidence_list: List[Dict[str, Any]],
                             verdict: str, confidence: float) -> str:
        supporting = [e for e in evidence_list if e['supports_claim']]
        contradicting = [e for e in evidence_list if not e['supports_claim']]

        if verdict == "SUPPORTED":
            high_cred_sources = [e for e in supporting if e['credibility_score'] > 0.7]
            avg_cred = (sum(e['credibility_score'] for e in supporting) / len(supporting)) if supporting else 0.0
            return (f"Strong evidence from {len(high_cred_sources)} high-credibility sources "
                    f"supports this claim. Average credibility: {avg_cred:.2f}")
        elif verdict == "REFUTED":
            high_cred_sources = [e for e in contradicting if e['credibility_score'] > 0.7]
            return (f"Strong contradicting evidence from {len(high_cred_sources)} credible sources "
                    f"refutes this claim. {len(contradicting)} sources contradict vs {len(supporting)} support")
        elif verdict == "MIXED":
            return (f"Conflicting evidence: {len(supporting)} sources support, {len(contradicting)} contradict. "
                    f"Credible sources on both sides prevent a definitive conclusion")
        else:
            return "Insufficient credible evidence available for verification"
