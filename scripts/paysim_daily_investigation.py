
"""Compare daily fraud investigation strategies on synthetic PaySim data.

Run:
    python scripts/paysim_daily_investigation.py

Strategies:
    amount_only:
        Prioritize highest transaction amounts.

    draining_amount:
        Prioritize account-draining behavior, then highest amounts.

Evaluation:
    - One simulated day = 24 PaySim hourly steps.
    - Maximum 1,000 reviews per simulated day, per strategy.
    - Eligible transactions: TRANSFER and CASH_OUT.
    - Original chronological split: step 323.
    - Day crossing the split is excluded from period summaries.
    - High-volume days have at least 100,000 eligible transactions.

Important:
    PaySim is synthetic.
    Fraud labels are never used for ranking.
    Rankings use the full day's transactions retrospectively.
    Holdout comparisons are exploratory because previous results
    have already been inspected.
    This is not validated real-world fraud performance.
"""

import csv
import heapq
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    ROOT
    / "data"
    / "external"
    / "PS_20174392719_1491204439457_log.csv"
)

DAILY_REVIEW_CAPACITY = 1000
HOURS_PER_DAY = 24
SPLIT_STEP = 323

HIGH_VOLUME_THRESHOLD = 100000

STRATEGIES = (
    "amount_only",
    "draining_amount",
)


def simulated_day(step):
    """Convert a PaySim hourly step into a simulated day."""
    return (step - 1) // HOURS_PER_DAY + 1


def account_draining(amount, old_balance, new_balance):
    """Identify an outgoing transaction that empties its sender."""
    return (
        old_balance > 0
        and new_balance == 0
        and amount >= old_balance
    )


def ranking_score(strategy, amount, drained):
    """Rank transactions using observable features only."""

    if strategy == "amount_only":
        return (amount,)

    if strategy == "draining_amount":
        return (
            int(drained),
            amount,
        )

    raise ValueError(f"Unknown strategy: {strategy}")


def update_queue(queue, candidate):
    """Keep the highest-ranked daily investigation candidates."""

    if len(queue) < DAILY_REVIEW_CAPACITY:
        heapq.heappush(queue, candidate)

    elif candidate > queue[0]:
        heapq.heapreplace(queue, candidate)


def evaluate_queue(queue, total_fraud):
    """Calculate review precision and fraud capture."""

    reviewed = len(queue)

    # Fraud labels are evaluation payload, not ranking features.
    fraud_captured = sum(
        candidate[2] for candidate in queue
    )

    precision = (
        fraud_captured / reviewed
        if reviewed else 0.0
    )

    capture_rate = (
        fraud_captured / total_fraud
        if total_fraud else 0.0
    )

    return {
        "reviewed": reviewed,
        "fraud_captured": fraud_captured,
        "precision": precision,
        "capture_rate": capture_rate,
    }


def workload_category(eligible_count):
    """Classify daily eligible transaction workload."""

    if eligible_count >= HIGH_VOLUME_THRESHOLD:
        return "High-volume"

    if eligible_count <= DAILY_REVIEW_CAPACITY:
        return "Full coverage"

    return "Lower-volume"


def period_for_day(min_step, max_step):
    """Assign only complete days to development or holdout."""

    if max_step <= SPLIT_STEP:
        return "Development"

    if min_step > SPLIT_STEP:
        return "Holdout"

    return "Split day"


def summarize_results(title, records):
    """Aggregate daily metrics using actual review counts."""

    print(f"\n===== {title} =====")

    if not records:
        print("No days in this category.")
        return

    days = {
        record["day"]
        for record in records
    }

    total_transactions = sum(
        record["transactions"]
        for record in records
    )

    total_eligible = sum(
        record["eligible"]
        for record in records
    )

    total_fraud = sum(
        record["fraud_labels"]
        for record in records
    )

    print(f"Simulated days: {len(days):,}")
    print(f"Transactions: {total_transactions:,}")
    print(f"Eligible transactions: {total_eligible:,}")
    print(f"Fraud labels: {total_fraud:,}")

    print(
        f"\n{'Strategy':<22}"
        f"{'Reviewed':>12}"
        f"{'Captured':>12}"
        f"{'Precision':>13}"
        f"{'Capture rate':>15}"
    )

    print("-" * 74)

    totals = {}

    for strategy in STRATEGIES:
        reviewed = sum(
            record["metrics"][strategy]["reviewed"]
            for record in records
        )

        captured = sum(
            record["metrics"][strategy]["fraud_captured"]
            for record in records
        )

        precision = (
            captured / reviewed
            if reviewed else 0.0
        )

        capture_rate = (
            captured / total_fraud
            if total_fraud else 0.0
        )

        totals[strategy] = {
            "reviewed": reviewed,
            "captured": captured,
            "precision": precision,
            "capture_rate": capture_rate,
        }

        print(
            f"{strategy:<22}"
            f"{reviewed:>12,}"
            f"{captured:>12,}"
            f"{precision:>12.2%}"
            f"{capture_rate:>14.2%}"
        )

    baseline = totals["amount_only"]
    selected = totals["draining_amount"]

    difference = (
        selected["captured"] - baseline["captured"]
    )

    print(
        "\nFraud labels captured difference "
        f"(draining_amount - amount_only): {difference:+,}"
    )

    if baseline["captured"] > 0:
        relative_change = (
            difference / baseline["captured"]
        )

        print(
            "Relative capture difference: "
            f"{relative_change:+.2%}"
        )
    else:
        print(
            "Relative capture difference: N/A "
            "(baseline captured zero fraud labels)"
        )


def main():
    if not DATA_PATH.is_file():
        raise FileNotFoundError(
            f"Missing PaySim dataset: {DATA_PATH}"
        )

    # Separate top-K queues for each simulated day
    # and each investigation strategy.
    daily_queues = defaultdict(
        lambda: {
            strategy: []
            for strategy in STRATEGIES
        }
    )

    daily_transactions = defaultdict(int)
    daily_eligible = defaultdict(int)
    daily_fraud = defaultdict(int)

    daily_min_step = {}
    daily_max_step = {}

    with DATA_PATH.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row_number, row in enumerate(reader, start=1):
            step = int(row["step"])
            day = simulated_day(step)

            actual_fraud = int(row["isFraud"])

            daily_transactions[day] += 1
            daily_fraud[day] += actual_fraud

            daily_min_step[day] = min(
                step,
                daily_min_step.get(day, step),
            )

            daily_max_step[day] = max(
                step,
                daily_max_step.get(day, step),
            )

            transaction_type = row["type"]

            if transaction_type not in (
                "TRANSFER",
                "CASH_OUT",
            ):
                continue

            daily_eligible[day] += 1

            amount = float(row["amount"])
            old_balance = float(row["oldbalanceOrg"])
            new_balance = float(row["newbalanceOrig"])

            drained = account_draining(
                amount,
                old_balance,
                new_balance,
            )

            for strategy in STRATEGIES:
                score = ranking_score(
                    strategy,
                    amount,
                    drained,
                )

                # Unique row order resolves exact score ties
                # before Python can compare the fraud label.
                #
                # The fraud label is evaluation payload only.
                candidate = (
                    score,
                    -row_number,
                    actual_fraud,
                )

                update_queue(
                    daily_queues[day][strategy],
                    candidate,
                )

    records = []

    for day in sorted(daily_transactions):
        period = period_for_day(
            daily_min_step[day],
            daily_max_step[day],
        )

        eligible = daily_eligible[day]

        category = workload_category(eligible)

        metrics = {}

        for strategy in STRATEGIES:
            metrics[strategy] = evaluate_queue(
                daily_queues[day][strategy],
                daily_fraud[day],
            )

        records.append({
            "day": day,
            "period": period,
            "category": category,
            "transactions": daily_transactions[day],
            "eligible": eligible,
            "fraud_labels": daily_fraud[day],
            "metrics": metrics,
        })

    print("\n===== PAYSIM DAILY STRATEGY COMPARISON =====")

    print(f"Simulated days: {len(records)}")
    print(f"Daily review capacity: {DAILY_REVIEW_CAPACITY:,}")
    print(f"Chronological split step: {SPLIT_STEP}")
    print(f"High-volume threshold: {HIGH_VOLUME_THRESHOLD:,}")
    print("Strategies: amount_only, draining_amount")

    print("\n===== DAILY COMPARISON =====")

    print(
        f"{'Day':>4} "
        f"{'Period':<12} "
        f"{'Workload':<14} "
        f"{'Eligible':>11} "
        f"{'Fraud':>7} "
        f"{'Reviews':>8} "
        f"{'Amount TP':>10} "
        f"{'Drain TP':>9} "
        f"{'Diff':>7}"
    )

    print("-" * 94)

    for record in records:
        amount_metrics = record["metrics"]["amount_only"]
        draining_metrics = record["metrics"]["draining_amount"]

        difference = (
            draining_metrics["fraud_captured"]
            - amount_metrics["fraud_captured"]
        )

        print(
            f"{record['day']:>4} "
            f"{record['period']:<12} "
            f"{record['category']:<14} "
            f"{record['eligible']:>11,} "
            f"{record['fraud_labels']:>7,} "
            f"{draining_metrics['reviewed']:>8,} "
            f"{amount_metrics['fraud_captured']:>10,} "
            f"{draining_metrics['fraud_captured']:>9,} "
            f"{difference:>+7,}"
        )

    # The split day is not included in either
    # development or holdout summaries.
    development = [
        record for record in records
        if record["period"] == "Development"
    ]

    holdout = [
        record for record in records
        if record["period"] == "Holdout"
    ]

    split_days = [
        record for record in records
        if record["period"] == "Split day"
    ]

    summarize_results(
        "DEVELOPMENT - ALL COMPLETE DAYS",
        development,
    )

    summarize_results(
        "HOLDOUT - ALL COMPLETE DAYS",
        holdout,
    )

    summarize_results(
        "HOLDOUT - HIGH-VOLUME DAYS",
        [
            record for record in holdout
            if record["category"] == "High-volume"
        ],
    )

    summarize_results(
        "HOLDOUT - LOWER-VOLUME DAYS",
        [
            record for record in holdout
            if record["category"] == "Lower-volume"
        ],
    )

    summarize_results(
        "HOLDOUT - FULL-COVERAGE DAYS",
        [
            record for record in holdout
            if record["category"] == "Full coverage"
        ],
    )

    if split_days:
        summarize_results(
            "SPLIT-DAY DIAGNOSTICS - EXCLUDED",
            split_days,
        )

    print("\n===== DATA QUALITY AND EVALUATION NOTES =====")

    for record in records:
        if record["category"] == "Full coverage":
            print(
                f"Day {record['day']}: "
                f"all {record['eligible']:,} eligible "
                "transactions fit within review capacity."
            )

    print(
        "\nDaily rankings are retrospective: "
        "all transactions from a simulated day are "
        "available before that day's top-K is selected."
    )

    print(
        "The 1,000-review capacity is an assumption, "
        "not an observed staffing constraint."
    )

    print(
        "Workload categories are descriptive. "
        "The 100,000-transaction threshold is not "
        "a fraud detection parameter."
    )

    print(
        "The original draining_amount strategy was "
        "selected in the earlier development evaluation."
    )

    print(
        "Holdout comparisons are exploratory because "
        "earlier holdout results have already been examined."
    )

    print(
        "PaySim is synthetic. Account-draining behavior "
        "may be closely related to how its fraud labels "
        "were generated."
    )

    print(
        "No results establish real-world effectiveness, "
        "live detection performance, or financial savings."
    )


if __name__ == "__main__":
    main()
