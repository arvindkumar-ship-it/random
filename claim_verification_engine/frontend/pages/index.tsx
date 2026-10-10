import { useState } from 'react';
import type { NextPage } from 'next';

interface VerificationResult {
  claim: string;
  verdict: string;
  confidence: number;
  reasoning: string;
  evidence_count: number;
  supporting_count: number;
  contradicting_count: number;
  processing_time_ms: number;
}

const VERDICT_STYLES: Record<string, { text: string; bg: string; label: string }> = {
  SUPPORTED: { text: 'text-verified', bg: 'bg-verified-soft', label: 'Supported' },
  REFUTED: { text: 'text-refuted', bg: 'bg-refuted-soft', label: 'Refuted' },
  MIXED: { text: 'text-mixed', bg: 'bg-mixed-soft', label: 'Mixed evidence' },
  UNVERIFIABLE: { text: 'text-unverifiable', bg: 'bg-unverifiable-soft', label: 'Unverifiable' },
};

const Home: NextPage = () => {
  const [claim, setClaim] = useState('');
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claim.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await fetch('/api/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: claim }),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || 'Verification failed');
      }
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const verdictStyle = result ? VERDICT_STYLES[result.verdict] : null;

  return (
    <div className="min-h-screen bg-paper font-sans text-ink">
      <div className="max-w-2xl mx-auto px-6 py-16 sm:py-24">
        <header className="mb-12">
          <p className="text-sm tracking-wide text-ink-soft mb-2">Claim Verification Engine</p>
          <h1 className="font-serif text-4xl sm:text-5xl leading-tight">
            Check a claim against the evidence
          </h1>
          <p className="mt-4 text-ink-soft leading-relaxed">
            Enter a factual statement. The engine decomposes it, retrieves supporting
            and contradicting sources, and returns a verdict with its reasoning.
          </p>
        </header>

        <form onSubmit={handleSubmit} className="mb-14">
          <label htmlFor="claim" className="sr-only">
            Claim to verify
          </label>
          <textarea
            id="claim"
            value={claim}
            onChange={(e) => setClaim(e.target.value)}
            placeholder="e.g. PM Modi inaugurated 5 new AIIMS in UP last week"
            className="w-full bg-transparent border border-line rounded-none px-4 py-3 text-ink placeholder:text-ink-soft/70 focus:outline-none focus:border-ink transition-colors resize-none"
            rows={3}
            required
          />
          <div className="flex items-center justify-between mt-4">
            <span className="text-xs text-ink-soft">
              {claim.length}/5000
            </span>
            <button
              type="submit"
              disabled={loading || !claim.trim()}
              className="px-6 py-2.5 bg-ink text-paper text-sm tracking-wide hover:bg-ink/85 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Verifying…' : 'Verify claim'}
            </button>
          </div>
        </form>

        {error && (
          <div className="mb-10 border-l-2 border-refuted pl-4 py-1 text-refuted text-sm">
            {error}
          </div>
        )}

        {result && verdictStyle && (
          <section className="border-t border-line pt-10">
            <div className="flex items-baseline justify-between gap-4 mb-6">
              <span
                className={`inline-block px-3 py-1 text-sm ${verdictStyle.bg} ${verdictStyle.text}`}
              >
                {verdictStyle.label}
              </span>
              <span className="text-sm text-ink-soft">
                {(result.confidence * 100).toFixed(0)}% heuristic score (uncalibrated)
              </span>
            </div>

            <p className="font-serif text-xl leading-snug mb-8">
              &ldquo;{result.claim}&rdquo;
            </p>

            <dl className="grid grid-cols-3 border-y border-line divide-x divide-line mb-8">
              <div className="px-4 py-4 text-center">
                <dt className="text-xs text-ink-soft mb-1">Supporting</dt>
                <dd className="font-serif text-2xl text-verified">{result.supporting_count}</dd>
              </div>
              <div className="px-4 py-4 text-center">
                <dt className="text-xs text-ink-soft mb-1">Contradicting</dt>
                <dd className="font-serif text-2xl text-refuted">{result.contradicting_count}</dd>
              </div>
              <div className="px-4 py-4 text-center">
                <dt className="text-xs text-ink-soft mb-1">Total evidence</dt>
                <dd className="font-serif text-2xl">{result.evidence_count}</dd>
              </div>
            </dl>

            <div className="mb-4">
              <p className="text-xs text-ink-soft mb-2">Reasoning</p>
              <p className="leading-relaxed text-ink/90 border-l-2 border-line pl-4">
                {result.reasoning}
              </p>
            </div>

            <p className="text-xs text-ink-soft/70 mt-8">
              Processed in {(result.processing_time_ms / 1000).toFixed(2)}s
            </p>
          </section>
        )}
      </div>
    </div>
  );
};

export default Home;
