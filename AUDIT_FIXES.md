# Truthful uncertainty and source matching

Repair branch: `fix/internship-audit-20261010`. Changes are scoped to audit findings; no deployment or live provider action is included.

## Changed

Credibility matching uses the actual hostname and domain boundaries, preventing trusted domains embedded in paths/lookalike hosts. Unknown coordinated sources no longer raise a lookup error. Removed invented statistical precision: empty/no validated evidence keeps bounds [0,1]. API and UI mark scores as uncalibrated heuristics.

## Verification

`cd claim_verification_engine && pytest -q tests/test_credibility.py`

Commands are entry points, not a claim that every live integration was executed. See the repair bundle for actual results.

## Setup and remaining evidence

Hardcoded domain weights are illustrative, not a verified external reputation database. Scores and [0,1] bounds have no demonstrated statistical coverage. Source independence, claim labels, retrieval quality, fairness, real provider integration and benchmark accuracy remain open. Build a labelled claim corpus and calibration protocol before representing these outputs as probabilities.

Full-suite check: the two existing live pipeline tests could not initialize their HTTP provider client in this environment (SOCKS transport dependency). The three offline regression checks are separate; no end-to-end claim is made.
