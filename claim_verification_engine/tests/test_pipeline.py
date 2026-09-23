import pytest
from app.services.pipeline import VerificationPipeline


@pytest.fixture
def pipeline():
    return VerificationPipeline()


@pytest.mark.asyncio
async def test_verify_simple_claim(pipeline):
    input_data = {
        'text': 'India won the Cricket World Cup in 2023',
        'claimed_timestamp': None
    }
    result = await pipeline.verify(input_data)

    assert result.claim == input_data['text']
    assert result.verdict in ['SUPPORTED', 'REFUTED', 'MIXED', 'UNVERIFIABLE']
    assert 0.0 <= result.confidence <= 1.0
    assert result.evidence_count >= 0


@pytest.mark.asyncio
async def test_verify_statistical_claim(pipeline):
    input_data = {
        'text': "India's GDP grew by 7.2% in Q2 2026",
        'claimed_timestamp': None
    }
    result = await pipeline.verify(input_data)

    assert result.evidence_count >= 0
    assert len(result.reasoning) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
