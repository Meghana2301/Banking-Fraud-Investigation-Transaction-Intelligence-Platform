# PaySim Fraud Analysis — Banking Transaction Intelligence Case Study

## 1. Business Problem

Fraud investigation teams must identify suspicious transactions while managing limited review capacity. A detection rule that generates too few alerts may miss important fraud cases, while an overly broad rule can overwhelm investigators with false positives.

**Business question:** How can transaction-level analysis improve fraud detection coverage while maintaining a manageable investigation workload?

This study evaluates an existing fraud flag and alternative transaction-amount thresholds using the public PaySim synthetic financial transaction dataset.

## 2. Dataset Overview

**Dataset:** PaySim — Synthetic Financial Transactions

**Source:** [PaySim on Kaggle](https://www.kaggle.com/datasets/ealaxi/paysim1)

| Metric | Result |
|---|---:|
| Total transactions | 6,362,620 |
| Fraud-labeled transactions | 8,213 |
| Non-fraud-labeled transactions | 6,354,407 |
| Fraud label rate | 0.1291% |
| Existing rule flags | 16 |
| Transaction types | 5 |
| Blank or missing values detected | 0 |

The dataset contains transaction types, amounts, sender and receiver identifiers, account balances, simulated time steps, fraud labels, and an existing fraud flag.

All transactions and fraud labels are simulated. The dataset does not contain verified real-world bank fraud outcomes.

## 3. Transaction Type Analysis

| Transaction Type | Total Transactions | Fraud-Labeled | Fraud Label Rate |
|---|---:|---:|---:|
| CASH_OUT | 2,237,500 | 4,116 | 0.1840% |
| PAYMENT | 2,151,495 | 0 | 0.0000% |
| CASH_IN | 1,399,284 | 0 | 0.0000% |
| TRANSFER | 532,909 | 4,097 | 0.7688% |
| DEBIT | 41,432 | 0 | 0.0000% |

### Key Finding — Fraud Labels Are Concentrated in Two Transaction Types

All 8,213 fraud-labeled transactions occur in `TRANSFER` and `CASH_OUT`.

`TRANSFER` has the highest fraud label rate at 0.7688%, approximately 4.2 times the rate observed for `CASH_OUT`.

However, `CASH_OUT` contains slightly more fraud-labeled transactions in absolute terms.

**Business implication:** Both transaction type and transaction volume matter when prioritizing investigation resources. A higher fraud rate does not necessarily mean a higher total number of fraud cases.

## 4. Existing Fraud Rule Evaluation

The dataset includes an `isFlaggedFraud` field representing an existing rule-generated flag.

Its performance was evaluated against the simulated `isFraud` label.

| Metric | Result |
|---|---:|
| True Positives | 16 |
| False Positives | 0 |
| True Negatives | 6,354,407 |
| False Negatives | 8,197 |
| Precision | 100.00% |
| Recall | 0.19% |
| False Positive Rate | 0.0000% |
| F1 Score | 0.39% |
| Investigation Queue | 16 |

### Key Finding — High Precision Does Not Guarantee Adequate Coverage

The existing flag achieved 100% precision on the simulated dataset because all 16 flagged transactions were fraud-labeled.

However, it detected only 16 of 8,213 fraud-labeled transactions, leaving 8,197 unflagged.

All 16 flagged transactions were `TRANSFER` transactions. Their amounts ranged from 353,874.22 to 10,000,000.00 in dataset units.

**Business implication:** The existing flag creates a minimal review queue but offers extremely limited fraud detection coverage in this simulation.

The exact underlying flagging logic was not established by this analysis.

## 5. Transaction Amount Threshold Analysis

Twelve exploratory rules were evaluated:

- Six amount thresholds for `TRANSFER`.
- Six amount thresholds for `CASH_OUT`.

The thresholds were 10,000; 50,000; 100,000; 250,000; 500,000; and 1,000,000.

Each rule was evaluated against the full dataset, using precision, recall, false positives, and investigation queue size.

### Selected Evaluation Results

| Detection Rule | Precision | Recall | False Positives | Investigation Queue |
|---|---:|---:|---:|---:|
| Existing PaySim Flag | 100.00% | 0.19% | 0 | 16 |
| TRANSFER ≥ 10,000 | 0.75% | 48.29% | 522,859 | 526,825 |
| TRANSFER ≥ 500,000 | 0.74% | 23.62% | 259,128 | 261,068 |
| CASH_OUT ≥ 500,000 | 3.61% | 23.43% | 51,309 | 53,233 |
| CASH_OUT ≥ 1,000,000 | 81.61% | 16.38% | 303 | 1,648 |

The complete results are generated locally in `data/paysim_threshold_results.csv`.

### Finding 1 — Low Thresholds Create Excessive Investigation Workload

The `TRANSFER ≥ 10,000` rule detected approximately 48.29% of all fraud-labeled transactions.

However, it generated 526,825 alerts, including 522,859 false positives.

**Business implication:** High detection coverage is not sufficient when the investigation queue is too large to manage.

### Finding 2 — Higher Thresholds Can Improve Alert Quality

The `CASH_OUT ≥ 1,000,000` rule achieved 81.61% precision with 1,648 alerts.

However, its recall was only 16.38%, meaning it missed most fraud-labeled transactions.

**Business implication:** High-value transaction rules may support targeted investigation, but they cannot provide comprehensive detection coverage by themselves.

### Finding 3 — A Single Amount Threshold Is Not Enough

The evaluated rules showed substantial trade-offs between precision, recall, and alert volume.

**Business implication:** Additional transaction characteristics and investigator capacity should be considered before selecting an alerting strategy.

## 6. Business Recommendations

**Recommendation 1 — Use multiple investigation signals**

Investigate combinations of transaction type, transaction amount, historical account behavior, and balance consistency rather than relying on a single amount threshold.

**Recommendation 2 — Prioritize manageable alert queues**

Evaluate candidate rules against realistic investigator capacity and estimated review time.

**Recommendation 3 — Analyze account-level behavior**

Use SQL window functions and aggregations to investigate unusual account activity, repeated transfers, rapid transactions, and abnormal balance changes.

**Recommendation 4 — Validate proposed rules**

Separate rule development from evaluation data, and test promising strategies on held-out simulated transactions before making performance claims.

**Recommendation 5 — Build decision-focused reporting**

Develop Power BI reporting that compares fraud detection coverage, false-positive volume, transaction patterns, and investigation workload.

## 7. Limitations and Assumptions

- PaySim contains simulated financial transactions and synthetic fraud labels.
- The results do not represent actual bank customer activity or verified fraud outcomes.
- Fraud is highly imbalanced, with approximately 0.1291% of transactions labeled fraudulent.
- Fraud labels are concentrated in two transaction types, which may reflect the simulation's design.
- Transaction amount thresholds were evaluated on the same dataset used for exploratory comparison.
- No independent validation has yet been performed for the proposed amount-based rules.
- Investigation cost, staffing capacity, and fraud-loss severity have not yet been incorporated.
- No claim is made that the tested thresholds are suitable for production fraud detection.

## 8. Conclusion

The PaySim analysis demonstrates that fraud detection effectiveness cannot be evaluated using precision or recall alone.

The existing flag achieved perfect precision on the simulated dataset but detected only 0.19% of fraud-labeled transactions.

Alternative amount-based rules improved detection coverage but, in several cases, generated hundreds of thousands of additional investigation alerts.

The results support a more balanced approach that considers detection coverage, alert quality, and operational workload.

**Final recommendation:** Continue with account-level behavioral analysis, advanced SQL investigation patterns, and capacity-aware rule evaluation before selecting a preferred detection strategy.

## 9. Reproducibility

The analysis can be reproduced using the following scripts:

- `scripts/paysim_profile.py` — Dataset profiling and transaction-type analysis.
- `scripts/paysim_rule_evaluation.py` — Existing fraud flag evaluation.
- `scripts/paysim_threshold_analysis.py` — Amount threshold sensitivity analysis.


