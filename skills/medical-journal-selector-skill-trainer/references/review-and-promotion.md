# Review, metrics and release gates

Review before answer reveal. Judges receive masked study materials, recommendations and sources, no version IDs, answer, previous judgments or change hypotheses. Journal names in the recommendation are visible because they are the object of review; the true publishing journal identity is hidden.

Check each recommended journal's identity, exact scope quote and manuscript-specific connection, article-type admission, actual method-policy evidence, hard constraints, and source support for every changing fact. Separate verified policy from a reasoned methodological assessment. Missing scope/admission evidence cannot become an eligible journal just because the manuscript resembles a published paper. Missing non-hard JCR/time data can empty those routes without invalidating a supported fit route.

Hard failures: fabricated/unsupported verified fact, wrong journal identity, fabricated scope quote, known article/method prohibition bypassed, user hard gate ignored, target-answer leakage, or individual acceptance guarantee. Record the precise claim, source and repair needed. Unavailable fields correctly marked unknown are not failures. An empty report avoids fabrication but does not count as usable coverage.

For paired V1/V2 comparison, judges choose A/B/tie based on supported useful recommendations, method reasoning, evidence calibration and unnecessary burden, with a source-based explanation. Two agreeing votes decide; otherwise a third judge reviews independently. An unresolved split remains unresolved and is reported, not assigned to the favored version.

Compute Hit@k against the evaluation-only fit sequence and record whether the target journal was discovered at all. Use all evaluated valid-input cases as denominator; do not drop non-hits or empty reports. Provide Wilson 95% intervals, per-stratum denominators, policy-change notes, and raw counts. Also report evidence-supported usable coverage (at least one eligible journal), unknown-field coverage, hard failures, independent-review disagreement, tokens and timing when observed.

Stage promotion gates: 100 completed development and 50 untouched final records; every final V1/V2 generation and two blind reviews sealed before reveal; zero unresolved V2 hard failures; V2 paired wins >= losses; V2 usable coverage >= V1; protected behavior/language/package/installation checks passed. No statistical-improvement claim follows from a non-inferiority gate alone. The model/provider and AI-only judgments limit external validity.

Failure at stage one permits exactly one authorized extension (100 new development + 50 new final). Exposed test cases can diagnose defects but are not new blind evidence. Failure at stage two stops with `GATES_NOT_PASSED`; model connectivity exhaustion stops with `RUNNER_UNAVAILABLE`; no publication claims either outcome succeeded. General Trainer use may have other user-agreed bounds recorded in its manifest.
