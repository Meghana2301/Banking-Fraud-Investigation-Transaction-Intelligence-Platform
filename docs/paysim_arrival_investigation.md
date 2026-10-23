# Fraud Investigation Prioritization: A Capacity-Constrained Banking Case Study

**Project:** Banking Fraud Investigation & Transaction Intelligence Platform  
**Domain:** Banking | Fraud Analytics | Transaction Intelligence  
**Dataset:** PaySim — Synthetic Mobile Money Transactions  
**Analysis Type:** Exploratory, Rule-Based Fraud Investigation Simulation  
**Evaluation:** Chronological Arrival Cohorts | 24-Hour Investigation Deadline

---

## 1. Executive Summary

Financial institutions process large volumes of transactions, but fraud investigation teams have limited capacity to review potentially suspicious activity.

The central business challenge is not simply identifying suspicious transactions. It is deciding **which transactions investigators should review first** when investigation capacity is limited.

This project evaluates two transaction-prioritization strategies using the PaySim synthetic financial transaction dataset:

- **Amount-only:** Prioritizes transactions with the highest monetary amounts.
- **Draining + amount:** Prioritizes transactions that exhibit account-draining behavior, using transaction amount as a secondary ranking factor.

Both strategies were evaluated under the same simulated operational constraints:

- Maximum of 1,000 investigation reviews per simulated day.
- Hourly investigation scheduling.
- A 24-hour alert review deadline.
- Chronological transaction processing.
- Fraud labels used for retrospective evaluation, not prioritization.

### Key Business Finding

During the exploratory holdout period, the draining + amount strategy reviewed **2,210 fraud-labeled transactions**, compared with **1,976** using amount-only prioritization.

This represents:

- **234 additional fraud-labeled transactions reviewed.**
- **11.84% relative improvement** in fraud capture.
- An increase in fraud capture rate from **43.24% to 48.36%**.
- An increase in investigation precision from **11.34% to 12.70%**.

However, more than 800,000 eligible transactions expired without review under each strategy.

**Business conclusion:** Account-draining prioritization improved investigation targeting in this synthetic simulation, but the much larger operational challenge is excessive alert volume relative to investigation capacity.

---

## 2. Business Problem

### Business Scenario

Consider a financial institution that processes millions of transactions across digital payment channels.

A transaction monitoring system identifies potentially suspicious activity and generates alerts for investigation.

However, the institution cannot manually investigate every transaction.

The fraud operations team must make decisions about:

1. Which transactions deserve immediate attention?
2. How should available investigation capacity be allocated?
3. Which prioritization rules identify more fraud within a fixed workload?
4. How many suspicious transactions expire before investigation?
5. Does a more targeted investigation strategy introduce additional delays?

A simple approach is to investigate the largest transactions first.

However, transaction amount alone may not adequately represent suspicious account behavior.

An alternative is to prioritize transactions where the originating account appears to be drained.

### Business Objective

**Determine whether account-draining prioritization improves the review of fraud-labeled transactions within a fixed investigation capacity and 24-hour review window.**

The objective is not to claim that fraud was prevented. It is to evaluate which strategy makes better use of simulated investigation resources.

---

## 3. Dataset and Transaction Characteristics

The analysis uses the publicly available PaySim synthetic mobile money transaction dataset.

PaySim represents simulated financial transactions and includes transaction amounts, account balances, transaction types, and fraud labels.

### Dataset Overview

| Metric | Value |
|---|---:|
| Total transactions | 6,362,620 |
| Fraud-labeled transactions | 8,213 |
| Overall fraud rate | Approximately 0.1291% |
| Simulated time steps | 743 |
| Hours per simulated day | 24 |
| Transaction types used for investigation | TRANSFER and CASH_OUT |

### Why These Transaction Types?

The investigation simulation focuses on `TRANSFER` and `CASH_OUT` transactions because these are the transaction types containing fraud labels in this PaySim dataset.

This is a dataset-specific analytical choice, not a recommendation that real banks should ignore other transaction types.

### Data Fields Used

| Field | Analytical Purpose |
|---|---|
| `step` | Determines chronological arrival and simulated time |
| `type` | Identifies eligible transaction categories |
| `amount` | Supports transaction-value prioritization |
| `oldbalanceOrg` | Original balance of the sending account |
| `newbalanceOrig` | Remaining balance of the sending account |
| `isFraud` | Ground-truth label used for evaluation |

The `isFraud` field is excluded from prioritization decisions.

It is used only to measure outcomes after simulated investigations are selected.

---

## 4. Investigation Strategies

Two prioritization strategies were compared.

### Strategy A: Amount-Only Prioritization

Transactions are ranked by monetary amount, with the largest transactions receiving the highest priority.

**Business rationale:** High-value transactions may represent greater potential financial exposure and are often useful starting points for risk-based investigation.

**Limitation:** Large transaction amounts do not necessarily indicate fraud. Legitimate high-value transactions may consume review capacity.

### Strategy B: Account-Draining + Amount Prioritization

Transactions are prioritized first by whether they exhibit account-draining behavior and then by monetary amount.

For this experiment, account-draining behavior is defined as:

- The originating account had a positive balance before the transaction.
- The originating account balance became zero after the transaction.
- The transaction amount was greater than or equal to the original account balance.

**Business rationale:** Transactions that deplete an account's available balance may warrant investigation, particularly when combined with other risk indicators.

**Important limitation:** PaySim's synthetic fraud-generation process may make account-draining behavior unusually predictive. The same effectiveness cannot be assumed for real banking transactions.

Neither strategy uses the fraud label when deciding review priority.

---

## 5. Investigation Simulation Methodology

The experiment was designed to simulate the operational constraints of a transaction investigation team.

### 5.1 Chronological Processing

Transactions are processed in ascending PaySim time-step order.

The system cannot prioritize transactions that have not yet arrived.

This avoids the unrealistic assumption that investigators know all future transactions at the beginning of the day.

### 5.2 Hourly Investigation Scheduling

Transactions arriving during a simulated hour become available for review at that hour's review opportunity.

The daily investigation capacity is distributed across hourly review opportunities.

The simulation assumes continuous 24-hour investigation coverage. It does not model individual analyst shifts or working hours.

### 5.3 Investigation Capacity

Both strategies operate under a maximum capacity of 1,000 reviews per simulated day.

This allows the experiment to compare prioritization effectiveness under a consistent workload constraint.

### 5.4 Alert Expiration

Each eligible transaction has a simulated 24-hour review window.

Transactions not reviewed within the allowed window are classified as expired.

Expired transactions are counted as unreviewed, not investigated.

This prevents the simulation from maintaining an unlimited investigation backlog indefinitely.

### 5.5 Arrival-Cohort Evaluation

Each transaction is assigned to a development or holdout cohort based on its arrival time.

The chronological boundary is PaySim step 323.

| Cohort | Eligible Transactions | Eligible Fraud Labels |
|---|---:|---:|
| Development | 1,951,895 | 3,643 |
| Holdout | 818,514 | 4,570 |

The split is based on arrival step rather than complete calendar days.

Transactions can be reviewed after their arrival cohort's boundary, provided they remain within their allowed review window.

This allows fraud capture to be measured against the transactions that actually arrived in each cohort.

### 5.6 Evaluation Metrics

The analysis measures:

**Investigation precision**

The percentage of reviewed transactions that have a fraud label.

**Fraud capture rate**

The percentage of eligible fraud-labeled transactions reviewed before expiration within their arrival cohort.

**Average investigation wait**

The average simulated time between transaction arrival and investigation review, for reviewed transactions.

**Expired fraud alerts**

The number of fraud-labeled eligible transactions that were not reviewed within the deadline.

**Review capacity utilization**

The percentage of available investigation review slots actually used.

---

## 6. Experimental Results

### 6.1 Development Cohort

| Metric | Amount-Only | Draining + Amount |
|---|---:|---:|
| Eligible transactions | 1,951,895 | 1,951,895 |
| Eligible fraud labels | 3,643 | 3,643 |
| Reviews completed | 13,097 | 13,070 |
| Fraud labels captured | 1,150 | 1,348 |
| Investigation precision | 8.78% | 10.31% |
| Fraud capture rate | 31.57% | 37.00% |
| Expired transactions | 1,938,798 | 1,938,825 |
| Expired fraud alerts | 2,493 | 2,295 |
| Average investigation wait | 7.02 hours | 8.69 hours |

**Development observation:** Draining + amount prioritization reviewed 198 additional fraud-labeled transactions while performing slightly fewer total reviews.

This provided initial evidence that the additional behavioral rule could improve investigation targeting.

### 6.2 Holdout Cohort

| Metric | Amount-Only | Draining + Amount |
|---|---:|---:|
| Eligible transactions | 818,514 | 818,514 |
| Eligible fraud labels | 4,570 | 4,570 |
| Reviews completed | 17,427 | 17,401 |
| Fraud labels captured | 1,976 | 2,210 |
| Investigation precision | 11.34% | 12.70% |
| Fraud capture rate | 43.24% | 48.36% |
| Expired transactions | 801,087 | 801,113 |
| Expired fraud alerts | 2,594 | 2,360 |
| Average investigation wait | 7.83 hours | 8.07 hours |

### Key Holdout Findings

**Finding 1 — Improved fraud investigation targeting**

The draining + amount strategy reviewed 234 more fraud-labeled transactions than the amount-only strategy.

This is an 11.84% relative increase in captured fraud labels.

**Finding 2 — Higher investigation precision**

Investigation precision improved from 11.34% to 12.70%.

The improvement indicates that a greater proportion of completed reviews corresponded to fraud-labeled transactions.

**Finding 3 — Fewer expired fraud alerts**

The draining strategy reduced expired fraud-labeled alerts from 2,594 to 2,360.

This is a reduction of 234 missed fraud-labeled investigation opportunities in the simulated review window.

**Finding 4 — Slightly longer average investigation wait**

Average investigation wait increased from 7.83 to 8.07 hours.

The difference is approximately 14 minutes.

This tradeoff deserves monitoring because review timing may matter for high-risk payment activity.

**Finding 5 — Severe alert-volume pressure**

Under both strategies, more than 800,000 eligible holdout transactions expired without review.

This demonstrates that investigation capacity is insufficient when every eligible TRANSFER and CASH_OUT transaction enters the review queue.

---

## 7. Investigation Capacity and Operational Efficiency

The simulation also measured overall investigation capacity utilization across the complete processing period, including the final review window.

| Metric | Amount-Only | Draining + Amount |
|---|---:|---:|
| Available review slots | 31,918 | 31,918 |
| Completed reviews | 30,524 | 30,471 |
| Capacity utilization | 95.63% | 95.47% |

Both strategies used approximately 95% of available review capacity.

This suggests that the investigation operation was generally capacity-constrained rather than lacking transactions to review.

However, high capacity utilization does not automatically mean operational efficiency.

A team can remain busy while still missing a large proportion of fraud-labeled activity.

**Analytical interpretation:** Improving the selection of transactions for investigation is more valuable than simply maximizing the number of occupied review slots.

The experiment also highlights the need to distinguish transaction eligibility from actionable alert generation.

The current simulation treats all TRANSFER and CASH_OUT transactions as investigation candidates, creating an unrealistically broad alert population for a typical manually reviewed workflow.

---

## 8. Business Recommendations

Based on the measured results, the following recommendations would be presented to a fraud operations or risk management team.

### Recommendation 1 — Improve Upstream Alert Screening

**Priority: High**

The most significant issue is excessive alert volume.

Before transactions enter the manual investigation queue, introduce an additional risk-screening stage that identifies a smaller population of potentially suspicious transactions.

Potential screening features for future evaluation include:

- Transaction amount relative to customer activity.
- Account balance changes.
- Unusual transaction frequency.
- Repeated transfers or cash-outs.
- Account-level behavioral anomalies.

These are proposed future features, not capabilities already validated in this experiment.

**Expected analytical benefit:** A smaller and more relevant alert population could make limited review capacity more effective. The magnitude of any improvement requires testing.

### Recommendation 2 — Retain Account-Draining Behavior as a Candidate Risk Signal

**Priority: High**

The draining + amount strategy outperformed amount-only ranking in both development and exploratory holdout results.

Account-draining behavior is therefore worth retaining as a candidate feature for further testing.

However, it should not be adopted as a production fraud rule based solely on PaySim.

Independent validation using representative transaction data is necessary.

### Recommendation 3 — Monitor Investigation Delays

**Priority: Medium**

The draining strategy improved capture while slightly increasing average review wait.

Future evaluations should include:

- Median investigation wait.
- 90th- and 95th-percentile wait times.
- Investigation delays for fraud-labeled transactions.
- Alerts reviewed near expiration.
- Fraud-labeled alerts missed because of expiration.

These measures would provide a clearer understanding of operational responsiveness.

### Recommendation 4 — Introduce Alert Lifecycle Management

**Priority: Medium**

A production investigation workflow should track alerts from generation through review, escalation, resolution, or expiration.

Relevant operational fields could include:

- Alert creation timestamp.
- Risk score or priority.
- Assigned investigation queue.
- Review timestamp.
- Investigation status.
- Expiration timestamp.
- Resolution outcome.

These fields would support auditability, workload monitoring, and operational reporting.

### Recommendation 5 — Validate on Independent Data Before Deployment

**Priority: Critical before production use**

The holdout data has already been examined during earlier project experiments.

Consequently, these holdout results are exploratory rather than an untouched independent validation.

Before deploying a similar strategy, a financial institution should evaluate it on genuinely unseen, representative transaction data and review the risk of false positives, missed fraud, and operational consequences.

---

## 9. Limitations and Risk Considerations

This case study is a simulation and has several important limitations.

**Synthetic dataset:** PaySim does not fully represent the complexity of real banking customers, transactions, fraud patterns, or investigator behavior.

**Potential synthetic signal bias:** Account-draining behavior may align closely with how PaySim generated fraudulent transactions.

**Simulated staffing:** The experiment assumes investigation capacity distributed over 24 hours, without modeling individual analyst shifts, staffing costs, breaks, or escalation processes.

**Simplified investigation outcome:** A reviewed fraud-labeled transaction is counted as captured for evaluation. This does not mean an investigator correctly confirmed fraud or prevented financial loss.

**No financial loss estimates:** The experiment does not establish prevented fraud value, recovered funds, operational cost savings, or return on investment.

**Limited alert lifecycle:** The model simulates review and expiration but does not include complete case management, customer contact, account restrictions, or regulatory reporting.

**Exploratory holdout:** The holdout was previously examined, limiting its value as independent evidence of generalization.

**Hourly time resolution:** All transactions within a simulated hour are available before that hour's review selection. Precise within-hour arrival and response times are unknown.

These limitations are essential when interpreting the results.

---

## 10. Final Business Decision

### Recommended Decision: Continue Research, Do Not Deploy

The experiment supports retaining account-draining behavior as a candidate fraud investigation prioritization signal.

The strategy demonstrated stronger fraud-label capture and investigation precision than amount-only prioritization under the tested assumptions.

However, the results do not justify production deployment.

The principal operational issue remains the mismatch between transaction volume and manual investigation capacity.

A more mature solution should combine:

1. Selective upstream alert generation.
2. Risk-based investigation prioritization.
3. Explicit investigation capacity management.
4. Alert expiration and lifecycle monitoring.
5. Independent validation and operational performance measurement.

**Final conclusion:** In this synthetic banking fraud investigation simulation, account-draining prioritization improved fraud-label capture by 11.84% relative to amount-only ranking under a 24-hour investigation deadline. The experiment demonstrates the value of behavioral prioritization, while highlighting that effective alert screening and investigation capacity management are equally important to a defensible fraud operations strategy.

---

## 11. Technical Implementation and Reproducibility

**Project:** Banking Fraud Investigation & Transaction Intelligence Platform

**Implementation:** Python-based chronological fraud investigation simulation.

**Core analytical techniques:**

- Transaction filtering and eligibility screening.
- Rule-based risk prioritization.
- Chronological transaction processing.
- Hourly review-capacity allocation.
- Priority-queue investigation scheduling.
- Alert expiration.
- Arrival-cohort evaluation.
- Investigation precision and fraud capture measurement.
- Operational backlog and capacity analysis.

**Implementation script:**

`scripts/paysim_arrival_investigation.py`

**Run command:**

```powershell
python scripts/paysim_arrival_investigation.py
```

The script reads the locally available PaySim CSV file from `data/external/`, performs the simulation, and prints development, holdout, and operational metrics.

The source dataset is not included in the repository and must be obtained separately.

### Project Deliverables

This case study complements the broader project components, including the original transaction analytics pipeline, fraud strategy comparison experiments, Snowflake/dbt development work, and Streamlit dashboard.

The PaySim investigation experiments are separate from the original transaction analytics dataset. Their metrics should not be represented as coming from the Snowflake/dbt pipeline or existing dashboard unless those integrations have actually been implemented and validated.

---

## 12. Portfolio Summary

**Business Problem:** Investigation teams have limited capacity to review high volumes of potentially suspicious banking transactions.

**Solution Evaluated:** A chronological, capacity-constrained fraud investigation simulation comparing amount-only prioritization with account-draining behavioral prioritization.

**Dataset:** 6.36 million synthetic PaySim transactions.

**Measured Result:** The draining + amount strategy reviewed 234 additional fraud-labeled transactions in the exploratory holdout, improving fraud capture from 43.24% to 48.36%.

**Business Insight:** Behavioral prioritization improved investigation targeting, but excessive alert volume remained the dominant operational limitation.

**Recommendation:** Strengthen upstream alert screening, retain draining behavior as a candidate risk signal, and conduct independent validation before operational deployment.