# Fraud Detection Rule Evaluation — Banking Analytics Case Study

## 1. Business Problem

Financial institutions must identify potentially fraudulent transactions while managing limited investigation resources. Excessive false alerts increase operational workload, while missed fraud can expose customers and institutions to financial risk.

**Business question:** Can behavioral transaction monitoring improve fraud detection coverage without creating an unsustainable investigation workload?

## 2. Dataset and Methodology

This analysis evaluates 5,000 simulated banking transactions, including 109 synthetic fraud labels.

Three fraud detection strategies were compared:

1. **Risk Score ≥ 65:** The existing transaction risk-scoring approach based on transaction amount, country, and channel.
2. **Behavioral Only:** Customer spending spikes and rapid transaction bursts, evaluated using historical transaction behavior.
3. **Combined OR:** A transaction is flagged when either the risk-score rule or the behavioral rule is triggered.

Performance was evaluated using confusion matrix metrics, precision, recall, F1 score, false-positive rate, and investigation queue size.

The analysis is reproducible using `scripts/fraud_strategy_comparison.py`.

## 3. Fraud Detection Evaluation Results

| KPI | Risk Score ≥ 65 | Behavioral Only | Combined OR |
|---|---:|---:|---:|
| True Positives | 87 | 53 | 98 |
| False Positives | 27 | 215 | 229 |
| True Negatives | 4,864 | 4,676 | 4,662 |
| False Negatives | 22 | 56 | 11 |
| Precision | 76.32% | 19.78% | 29.97% |
| Recall | 79.82% | 48.62% | 89.91% |
| F1 Score | 78.03% | 28.12% | 44.95% |
| Investigation Queue | 114 | 268 | 327 |

## 4. Key Analytical Findings

### Finding 1 — The baseline rule provides stronger precision

The existing risk-score rule achieved 76.32% precision while generating 114 investigation alerts. It correctly identified 87 of the 109 synthetic fraud-labeled transactions.

Among the three evaluated strategies, the baseline also achieved the highest F1 score at 78.03%.

**Business implication:** The baseline offers a more selective alerting approach, reducing unnecessary investigations compared with the alternatives.

### Finding 2 — Behavioral monitoring provides additional detection coverage

The behavioral detection strategy identified 53 fraud-labeled transactions, including 11 that were missed by the baseline risk-score rule.

However, the behavioral approach generated 268 alerts, of which 215 were false positives. Its precision was 19.78%.

**Business implication:** Behavioral monitoring provides complementary detection signals but creates substantial additional investigation workload when used independently.

### Finding 3 — Combining rules improves recall but increases workload

The combined strategy increased recall from 79.82% to 89.91%, identifying 98 of the 109 fraud-labeled transactions.

However, investigation volume increased from 114 to 327 alerts, representing approximately 187% more alerts than the baseline.

Precision also decreased from 76.32% to 29.97%.

**Business implication:** Increasing fraud detection coverage can significantly increase operational workload and reduce alert quality.

### Finding 4 — Additional detection comes with an investigation cost

Compared with the baseline, the combined strategy generated:

- 11 additional true positives.
- 202 additional false positives.
- 213 additional investigation alerts.
- 11 fewer missed fraud-labeled transactions.

This represents approximately 19.4 additional investigations for every additional fraud-labeled transaction identified.

**Business implication:** Fraud detection strategies should be evaluated using both detection performance and operational efficiency, rather than recall alone.

## 5. Business Recommendations

**Recommendation 1 — Retain the baseline strategy for further evaluation**

Maintain the existing risk-score threshold of 65 as the initial comparison baseline rather than immediately enabling all behavioral alerts.

**Recommendation 2 — Investigate selective behavioral alerting**

Evaluate whether behavioral signals can improve alert prioritization or support secondary review without automatically expanding the primary investigation queue.

**Recommendation 3 — Incorporate investigation capacity**

Analyze how different risk thresholds affect alert volumes, estimated investigation time, and the number of cases investigators can review.

**Recommendation 4 — Validate against an independent dataset**

Evaluate the detection strategies using a separate public fraud dataset before drawing broader conclusions about effectiveness.

**Recommendation 5 — Strengthen executive reporting**

Develop Power BI reporting that compares detection coverage, false positives, investigator workload, and operational trade-offs to support management decisions.

## 6. Limitations and Assumptions

- All transactions and fraud labels used in this evaluation are synthetic.
- Synthetic fraud labels were generated using transaction characteristics that overlap with the risk-scoring rules. This may inflate measured performance.
- The findings do not represent actual TD Bank transactions, customer records, or production fraud detection results.
- The behavioral analysis identified 268 spending spikes and zero rapid transaction bursts. Therefore, behavioral detection results in this dataset reflect spending-spike detection only.
- Investigation costs, fraud-loss severity, staffing constraints, and review capacity have not yet been incorporated into the analysis.
- The results describe performance on the generated dataset and do not establish how these strategies would perform on independent banking transactions.

## 7. Conclusion

The evaluation demonstrates that maximizing fraud detection recall does not necessarily produce the most operationally effective investigation strategy.

Although combining transaction risk scores with behavioral signals increased recall to 89.91%, it also increased the investigation queue from 114 to 327 alerts and reduced precision to 29.97%.

The baseline risk-score strategy achieved the highest F1 score among the three evaluated approaches, making it a reasonable starting point for further analysis.

**Final recommendation:** Retain the baseline as the comparison strategy, investigate selective behavioral alert prioritization, and validate the findings using an independent public fraud dataset before recommending operational changes.

The next phase will focus on public dataset integration, followed by threshold sensitivity, investigation workload analysis, advanced SQL, and Power BI executive reporting.