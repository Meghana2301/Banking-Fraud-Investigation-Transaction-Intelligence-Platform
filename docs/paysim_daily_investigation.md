# PaySim Daily Fraud Investigation Prioritization — Case Study

## 1. Executive Summary

This experiment evaluates whether an explainable account-draining prioritization strategy can improve fraud investigation efficiency compared with an amount-only baseline.

The evaluation uses the **synthetic PaySim mobile-money dataset** and assumes a maximum capacity of **1,000 transaction reviews per simulated day**.

Across 17 complete simulated holdout days, the account-draining strategy captured **2,204 fraud-labeled transactions**, compared with **1,951** using amount-only prioritization, with the same 16,272 reviews per strategy.

This represents **253 additional fraud labels captured (12.97% relative increase)** in a retrospective synthetic-data evaluation.

The improvement was not consistent across workloads and was concentrated in lower-volume days.

## 2. Dataset and Investigation Scope

- Dataset: PaySim synthetic mobile-money transactions.
- Total dataset: 6,362,620 transactions.
- Total fraud labels: 8,213.
- Eligible investigation types: `TRANSFER` and `CASH_OUT`.
- Simulated day: 24 consecutive PaySim hourly steps.
- Maximum review capacity: 1,000 eligible transactions per day, per strategy.
- Chronological development/holdout split: PaySim step 323.
- Day 14 crosses the split boundary and is excluded from development and holdout summaries.

All transaction rankings use observable transaction attributes. Fraud labels are used only to evaluate selected transactions.

## 3. Investigation Strategies

### Strategy A — Amount-Only Baseline

Eligible transactions are ranked by transaction amount, highest first.

This provides a simple baseline for evaluating whether additional transaction behavior improves investigation prioritization.

### Strategy B — Account Draining + Amount

Eligible transactions are ranked using the following priority:

1. Whether the transaction empties the sender's account, defined as `oldbalanceOrg > 0`, `newbalanceOrig == 0`, and `amount >= oldbalanceOrg`.
2. Transaction amount, highest first.
3. Original dataset row order to resolve exact ranking ties deterministically.

The `draining_amount` strategy was selected in an earlier development-period experiment and was not selected based on the daily holdout comparison.

## 4. Evaluation Methodology

The script streams PaySim transactions and maintains independent top-ranked investigation queues for each simulated day and strategy.

Each queue retains up to 1,000 eligible transactions. The strategies use identical review budgets and eligible transaction populations.

Reported metrics include:

- **Fraud captured:** Number of fraud-labeled transactions selected for review.
- **Precision:** Fraud-labeled transactions divided by reviewed transactions.
- **Fraud capture rate:** Fraud-labeled transactions captured divided by all fraud labels in the evaluated period.
- **Review workload:** Total transactions selected for investigation.

The evaluation is retrospective: each day's ranking uses the full day's transactions. It does not simulate real-time decision-making or measure operational detection latency.

## 5. Development-Period Results

| Metric | Amount-only | Draining + amount |
|---|---:|---:|
| Simulated days | 13 | 13 |
| Transactions reviewed | 12,429 | 12,429 |
| Fraud captured | 999 | 1,259 |
| Precision | 8.04% | 10.13% |
| Fraud capture rate | 28.37% | 35.76% |

The draining strategy captured 260 additional fraud labels, a 26.03% relative increase over amount-only ranking.

## 6. Exploratory Holdout Results

| Metric | Amount-only | Draining + amount |
|---|---:|---:|
| Simulated days | 17 | 17 |
| Transactions reviewed | 16,272 | 16,272 |
| Fraud captured | 1,951 | 2,204 |
| Precision | 11.99% | 13.54% |
| Fraud capture rate | 43.88% | 49.57% |

The draining strategy captured 253 additional fraud labels at the same review workload, a 12.97% relative increase.

These holdout results are **exploratory**, because earlier holdout outcomes had already been examined before this daily comparison.

## 7. Workload-Segmented Holdout Analysis

Daily workloads are categorized using the number of eligible `TRANSFER` and `CASH_OUT` transactions.

- **High-volume:** At least 100,000 eligible transactions per day.
- **Lower-volume:** More than 1,000 but fewer than 100,000 eligible transactions.
- **Full coverage:** At most 1,000 eligible transactions, allowing every eligible transaction to be reviewed.

| Workload category | Days | Amount-only captured | Draining captured | Difference |
|---|---:|---:|---:|---:|
| High-volume | 3 | 123 | 128 | +5 |
| Lower-volume | 13 | 1,556 | 1,804 | +248 |
| Full coverage | 1 | 272 | 272 | 0 |
| **Total** | **17** | **1,951** | **2,204** | **+253** |

Approximately 98% of the additional fraud labels captured came from lower-volume days.

On high-volume holdout days, the draining strategy captured only five additional fraud labels across 3,000 reviews.

This demonstrates that the observed benefit depends substantially on investigation workload.

## 8. Synthetic Data Anomalies

Two simulated days have fewer eligible transactions than the assumed daily review capacity:

- Day 3: 429 eligible transactions.
- Day 31: 272 eligible transactions.

On Day 31, all 272 transactions are fraud-labeled: 136 `TRANSFER` and 136 `CASH_OUT`.

Both strategies therefore achieve 100% precision and fraud capture on that day because all eligible transactions can be reviewed.

This result should not be interpreted as perfect fraud detection.

Day 31 is retained in the overall results and reported separately as a full-coverage day.

## 9. Limitations

**Synthetic-data dependence:** PaySim does not represent a validated sample of real-world banking activity. Account-draining behavior may be closely connected to the dataset's fraud-generation mechanism.

**Retrospective daily selection:** Transactions are ranked using the full day's available records. The experiment does not simulate live alerts, streaming decisions, or investigation delays.

**Assumed review capacity:** The 1,000-review daily limit is an experimental assumption, not a measured analyst staffing constraint.

**Uneven daily workloads:** Transaction volume varies dramatically between simulated days, influencing the fraction of transactions that investigators can review.

**Exploratory holdout analysis:** The holdout was previously examined, so this comparison should not be described as independent, untouched validation.

**No verified business savings:** The experiment does not measure financial losses prevented, analyst hours saved, investigation costs, or real-world false-positive outcomes.

## 10. Conclusions and Next Steps

The experiment demonstrates that account-draining prioritization can capture more fraud-labeled transactions than amount-only ranking under equal daily review budgets in the synthetic PaySim dataset.

However, most of the observed advantage occurs during lower-volume simulated days. The improvement is much smaller during high-volume holdout periods.

The appropriate next steps are to evaluate chronological arrival-based prioritization, investigate workload sensitivity, and assess the strategy on a separate dataset before making stronger generalization claims.

**Overall conclusion:** This is an explainable, reproducible investigation-prioritization experiment, not a production-validated fraud detection system.