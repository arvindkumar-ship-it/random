import networkx as nx
from urllib.parse import urlsplit
from typing import List, Dict, Any


class SourceCredibilityAnalyzer:
    def __init__(self):
        self.graph = nx.DiGraph()
        self._load_credibility_database()

    def _load_credibility_database(self):
        """Illustrative hardcoded weights; these are not independently verified ratings."""
        credibility_ratings = {
            'pib.gov.in': {'factual_reporting': 0.95, 'bias': 0.1},
            'thehindu.com': {'factual_reporting': 0.9, 'bias': 0.2},
            'indianexpress.com': {'factual_reporting': 0.88, 'bias': 0.25},
            'reuters.com': {'factual_reporting': 0.95, 'bias': 0.15},
            'apnews.com': {'factual_reporting': 0.95, 'bias': 0.1},
            'twitter.com': {'factual_reporting': 0.4, 'bias': 0.5},
            'facebook.com': {'factual_reporting': 0.35, 'bias': 0.5},
            'youtube.com': {'factual_reporting': 0.5, 'bias': 0.4},
            'wikipedia.org': {'factual_reporting': 0.85, 'bias': 0.2},
            'bbc.com': {'factual_reporting': 0.9, 'bias': 0.2},
        }
        for domain, ratings in credibility_ratings.items():
            self.graph.add_node(domain, **ratings)

    def add_source_relationship(self, source1: str, source2: str,
                                 relationship_type: str, strength: float):
        """Add edge between sources (cites, contradicts, etc.)"""
        self.graph.add_edge(source1, source2, type=relationship_type, weight=strength)

    def calculate_credibility_score(self, domain: str) -> float:
        """Uncalibrated source-weight heuristic; normalize host before matching."""
        parsed = urlsplit(domain if "://" in domain else "//" + domain)
        domain = (parsed.hostname or "").lower().rstrip(".")
        if not domain or (parsed.scheme and parsed.scheme not in {"http", "https"}):
            return 0.5
        if domain not in self.graph:
            # Unknown domain: check parent domain / known TLD patterns
            known_patterns = {
                'gov.in': 0.9,
                'nic.in': 0.85,
                'ac.in': 0.8,
                '.org': 0.7,
                '.com': 0.55
            }
            for pattern, score in known_patterns.items():
                suffix = pattern.lstrip(".")
                if domain == suffix or domain.endswith("." + suffix):
                    return score
            return 0.5

        base_score = self.graph.nodes[domain].get('factual_reporting', 0.5)

        # Adjust based on incoming citations from credible sources
        incoming_edges = list(self.graph.in_edges(domain, data=True))
        if incoming_edges:
            citation_boost = sum(
                self.graph.nodes[src].get('factual_reporting', 0.5) * data.get('weight', 0.5)
                for src, _, data in incoming_edges
            ) / len(incoming_edges)
            base_score = 0.7 * base_score + 0.3 * citation_boost

        return min(max(base_score, 0.0), 1.0)

    def detect_coordinated_behavior(self, sources: List[str]) -> Dict[str, Any]:
        """Detect coordinated inauthentic behavior"""
        if len(sources) < 2:
            return {'coordinated_likelihood': 0.1, 'network_density': 0.0}

        subgraph = self.graph.subgraph(sources)
        avg_credibility = (
            sum(self.calculate_credibility_score(s) for s in sources) / len(sources)
        )
        density = nx.density(subgraph)

        return {
            'sources_analyzed': sources,
            'average_credibility': avg_credibility,
            'coordinated_likelihood': max(0.0, 1.0 - avg_credibility),
            'network_density': density
        }
