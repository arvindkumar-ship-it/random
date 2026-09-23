from typing import List, Dict, Any
from groq import Groq
from app.config import settings
import json


class ClaimExtractor:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY, timeout=15.0, max_retries=1)

    def extract(self, text: str) -> List[Dict[str, Any]]:
        """Extract atomic claims from text"""
        prompt = f"""
        Extract all factual claims from the following text. For each claim, identify:
        - predicate (action/event)
        - subject (who)
        - object (what/whom)
        - quantifier (number, if any)
        - location (if mentioned)
        - timestamp (if mentioned)

        Return as a JSON object with a single key "claims" containing a list of dictionaries.

        Text: {text}

        Example output format:
        {{
          "claims": [
            {{
              "predicate": "inaugurated",
              "subject": "PM Modi",
              "object": "AIIMS hospital",
              "quantifier": 5,
              "location": "Uttar Pradesh",
              "timestamp": "last week"
            }}
          ]
        }}
        """

        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        try:
            claims_data = json.loads(response.choices[0].message.content)
            return claims_data.get('claims', []) if isinstance(claims_data, dict) else claims_data
        except Exception:
            return []

    def extract_entities(self, claim: Dict[str, Any]) -> set:
        """Extract key entities for matching"""
        entities = set()
        if claim.get('subject'):
            entities.add(claim['subject'].lower())
        if claim.get('object'):
            entities.add(claim['object'].lower())
        if claim.get('location'):
            entities.add(claim['location'].lower())
        if claim.get('quantifier'):
            entities.add(str(claim['quantifier']))
        return entities

    def classify_stance(self, claim_text: str, snippets: List[str]) -> List[str]:
        """
        For each evidence snippet, classify whether it SUPPORTS, CONTRADICTS,
        or is NEUTRAL/unrelated to the claim. This is the step that was missing
        before — evidence_retriever used to hardcode every result as supporting.
        Returns a list of 'support' | 'contradict' | 'neutral', same length/order as snippets.
        """
        if not snippets:
            return []

        numbered = "\n".join(f"{i+1}. {s[:400]}" for i, s in enumerate(snippets))
        prompt = f"""
        Claim: "{claim_text}"

        For each numbered evidence snippet below, decide if it SUPPORTS the claim,
        CONTRADICTS the claim, or is NEUTRAL (unrelated / doesn't confirm or deny it).
        Be strict: a snippet that debunks, corrects, or states the opposite of the
        claim is CONTRADICT, even if it mentions the same topic.

        Evidence:
        {numbered}

        Return a JSON object: {{"stances": ["support"|"contradict"|"neutral", ...]}}
        with exactly {len(snippets)} entries, in the same order as the evidence above.
        """

        try:
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            stances = data.get('stances', [])
            # Pad/truncate defensively so it always aligns with input length
            stances = [s if s in ('support', 'contradict', 'neutral') else 'neutral' for s in stances]
            if len(stances) < len(snippets):
                stances += ['neutral'] * (len(snippets) - len(stances))
            return stances[:len(snippets)]
        except Exception as e:
            print(f"Stance classification error: {e}")
            return ['neutral'] * len(snippets)
