from typing import Dict, Any
import asyncio
import time

from .claim_extractor import ClaimExtractor
from .evidence_retriever import EvidenceRetriever
from .osint_verifier import TemporalVerifier, GeolocationVerifier
from .source_credibility import SourceCredibilityAnalyzer
from .bayesian_verifier import BayesianVerifier
from .verdict_engine import FinalVerdictEngine
from app.config import settings
from app.models.schemas import VerificationResult, VerdictType
from app.utils.embeddings import get_embeddings_batch


class VerificationPipeline:
    def __init__(self):
        self.claim_extractor = ClaimExtractor()
        self.evidence_retriever = EvidenceRetriever()
        self.temporal_verifier = TemporalVerifier()
        self.geolocation_verifier = GeolocationVerifier()
        self.source_analyzer = SourceCredibilityAnalyzer()
        self.bayesian_verifier = BayesianVerifier()  # reused here for real recency/relevance scoring
        self.verdict_engine = FinalVerdictEngine(
            supported_threshold=settings.SUPPORTED_THRESHOLD,
            refuted_threshold=settings.REFUTED_THRESHOLD
        )

    async def verify(self, input_data: Dict[str, Any]) -> VerificationResult:
        start_time = time.time()

        # Step 1: Extract atomic claims (blocking LLM call, run off the event loop)
        atomic_claims = await asyncio.to_thread(self.claim_extractor.extract, input_data['text'])
        if not atomic_claims:
            # Fallback: treat entire text as a single claim
            atomic_claims = [{'predicate': 'claim', 'subject': input_data['text'][:100]}]

        # Step 2: Retrieve evidence for each claim
        all_evidence = []
        for claim in atomic_claims[:3]:  # Max 3 claims for performance
            evidence = await self.evidence_retriever.search(claim)

            # Step 3: Verify each evidence item
            for ev in evidence:
                # Temporal verification (only possible when we actually found a real date)
                if input_data.get('claimed_timestamp') and ev.get('publication_date'):
                    temporal_check = self.temporal_verifier.verify_temporal_consistency(
                        input_data['claimed_timestamp'],
                        ev['publication_date']
                    )
                    ev['temporal_verified'] = temporal_check['consistent']

                # Source credibility
                ev['credibility_score'] = self.source_analyzer.calculate_credibility_score(
                    ev['source_domain']
                )

                # Entity overlap calculation
                claim_entities = self.claim_extractor.extract_entities(claim)
                ev['entity_overlap'] = self._calculate_entity_overlap(
                    claim_entities, ev['snippet']
                )

            # Stance classification: does each snippet actually support or
            # contradict the claim? (blocking LLM call, run off the event loop)
            stances = await asyncio.to_thread(
                self.claim_extractor.classify_stance,
                input_data['text'],
                [ev['snippet'] for ev in evidence]
            )
            for ev, stance in zip(evidence, stances):
                ev['supports_claim'] = (stance == 'support')
                ev['stance'] = stance

            # Real relevance: cosine similarity between claim and each snippet's
            # local embedding (was previously a hardcoded 0.75 for every result)
            if evidence:
                texts = [input_data['text']] + [ev['snippet'] for ev in evidence]
                embeddings = await asyncio.to_thread(get_embeddings_batch, texts)
                claim_emb, snippet_embs = embeddings[0], embeddings[1:]
                for ev, snip_emb in zip(evidence, snippet_embs):
                    ev['relevance_score'] = max(0.0, min(1.0,
                        self.bayesian_verifier.calculate_cosine_similarity(claim_emb, snip_emb)
                    ))

            # Real recency: exponential decay from the page's own extracted
            # publish date (was previously a hardcoded 0.75-0.85, always "recent")
            for ev in evidence:
                if ev.get('publication_date'):
                    ev['recency_score'] = self.bayesian_verifier.calculate_recency_score(ev['publication_date'])
                    ev['temporal_confidence'] = 'known'
                else:
                    ev['recency_score'] = 0.5  # honestly unknown — neutral, not faked as recent
                    ev['temporal_confidence'] = 'unknown'
                    ev['publication_date'] = None

            # Drop neutral/unrelated evidence — it shouldn't move the verdict
            # either way, and keeping it would silently count as "not contradicting"
            evidence = [ev for ev in evidence if ev.get('stance') != 'neutral']

            all_evidence.extend(evidence)

        # Step 4: Generate final verdict
        verdict_data = self.verdict_engine.generate_verdict(
            input_data['text'],
            all_evidence
        )

        processing_time = (time.time() - start_time) * 1000

        result = VerificationResult(
            claim=input_data['text'],
            verdict=VerdictType(verdict_data['verdict']),
            confidence=verdict_data['confidence'],
            confidence_interval=verdict_data['score_bounds'],
            reasoning=verdict_data['reasoning'],
            evidence_count=verdict_data['evidence_count'],
            supporting_count=verdict_data['supporting_count'],
            contradicting_count=verdict_data['contradicting_count'],
            evidence_list=[self._convert_evidence(e) for e in all_evidence],
            method_scores=verdict_data['method_scores'],
            processing_time_ms=processing_time
        )

        return result

    def _calculate_entity_overlap(self, claim_entities: set, snippet: str) -> float:
        """Calculate Jaccard similarity between claim entities and evidence snippet"""
        snippet_words = set(snippet.lower().split())
        if not claim_entities or not snippet_words:
            return 0.5
        intersection = claim_entities.intersection(snippet_words)
        union = claim_entities.union(snippet_words)
        return len(intersection) / len(union) if union else 0.5

    def _convert_evidence(self, ev: Dict[str, Any]) -> Dict[str, Any]:
        """Convert evidence dict to schema format"""
        return {
            'source_url': ev['source_url'],
            'source_domain': ev['source_domain'],
            'snippet': ev['snippet'],
            'publication_date': ev['publication_date'],
            'supports_claim': ev['supports_claim'],
            'credibility_score': ev['credibility_score'],
            'recency_score': ev['recency_score'],
            'relevance_score': ev['relevance_score'],
            'entity_overlap': ev['entity_overlap'],
            'temporal_verified': ev.get('temporal_verified'),
            'geolocation_verified': ev.get('geolocation_verified')
        }
