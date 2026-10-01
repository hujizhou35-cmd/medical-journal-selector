# Medical methods: read the applicable rows

These checks identify journal-method fit and questions for the author; they are not a comprehensive peer review or acceptance predictor. Read actual methods, not only the title. Cite the relevant manuscript section in the profile.

| Study family | What changes journal selection |
|---|---|
| Clinical trials | Intervention, phase, prospective registration, comparator, outcomes, protocol and reporting requirements. Check actual journal policy; do not infer a registration waiver. |
| Cohort/case-control/cross-sectional | Population, recruitment, follow-up, confounding, missingness and causal claims. An association study is not an intervention-effect study. |
| Nursing/qualitative/mixed methods | Clinical or organizational question, setting, sampling, qualitative approach, reflexivity and intended nursing readership. A small qualitative sample does not imply poor fit by itself. |
| Public surveys / NHANES | Survey cycles, weights and complex sampling, exposure/outcome timing, overlap, multiple testing and clinical/public-health question. Review recent 24-month precedents and current database-analysis policies. |
| MIMIC/eICU/registry research | Site/time overlap, clinical endpoint, repeated admissions, selection and transportability. A different table or time split is not automatically an independent cohort. |
| Prediction/AI | Distinguish development, internal validation, temporal validation and external validation. Check whether preprocessing/tuning saw test data, calibration, population shift and intended use. Assess against journal expectations, not a universal “must add AI” rule. |
| Omics/bioinformatics | Discovery data, genuinely independent validation, batch effects, replication and biological interpretation. Public-dataset overlap can invalidate claimed replication. Check whether wet-lab validation is explicitly required for this journal/article. |
| Network pharmacology/toxicology | Database provenance, predicted vs demonstrated mechanisms, docking vs experimental confirmation. Docking alone is not independent biological validation. Look for journal-specific computational-only restrictions. |
| Mendelian randomization | Instrument validity, population overlap, directionality, sensitivity and replication. Combining GWAS sources alone does not prove causal validity or satisfy every publisher's validation rules. |
| Systematic review/Meta analysis | Question, eligible designs, protocol, search coverage, bias assessment, synthesis and reporting requirements; distinguish narrative reviews. Check whether unsolicited reviews are accepted. |
| Bibliometrics | Database coverage, search reproducibility, author/institution disambiguation and interpretation. Citation maps are not clinical efficacy evidence. Some publishers impose multi-database requirements: read current rules rather than generalize. |
| Case report/series | Explicit acceptance of case reports, consent, privacy and educational point. General medical scope is not proof this article type is accepted. |
| Basic/animal/in-vitro | Mechanism, model relevance, controls, replication, reporting and ethics requirements. Do not recommend irrelevant clinical journals solely on a disease keyword. |

## Validation labels

- **Internal:** random split, cross-validation or bootstrap within the development population.
- **Temporal:** later period; report possible overlap and same-setting limitations.
- **External:** genuinely independent participants/settings, with no training/tuning contamination. Describe independence rather than relying on the label.
- **Replication:** independently tests a finding; not necessarily validation of a predictive model.
- **Experimental:** tests a computational biological claim with appropriate experiments; do not equate it with clinical validation.
- **Unknown:** full methods missing or independence unclear; ask a focused question.

Record strengths and gaps with manuscript evidence. If a missing element violates a confirmed journal rule, exclude or make the candidate conditional. If it is your assessment rather than a rule, label it as such. No invented probabilities, mandatory “extra databases,” or automatic penalty for using public data.

Do not invent unspecified recruitment periods, sites or participant overlap. A cross-sectional design alone does not prove all data came from one period or rule out independent repeated cross-sectional datasets. A stated random split establishes internal splitting; describe other independence details as unknown unless the manuscript supplies them.
