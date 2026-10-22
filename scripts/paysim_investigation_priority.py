
"""Evaluate PaySim fraud investigation prioritization strategies.

Run:
    python scripts/paysim_investigation_priority.py

PaySim is a synthetic mobile-money dataset.

The script compares explainable investigation ranking strategies
on chronological development and holdout periods.

Fraud labels are used only for evaluation, never for ranking.
Results do not represent validated real-world fraud performance.
"""

import csv
import heapq
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    ROOT
    / "data"
    / "external"
    / "PS_20174392719_1491204439457_log.csv"
)

REVIEW_CAPACITY = 1000
TRAIN_FRACTION = 0.70

STRATEGIES = (
    "amount_only",
    "draining_amount",
    "draining_transfer_amount",
    "draining_small_balance",
)


def account_draining(amount, old_balance, new_balance):
    """Detect an outgoing transaction that empties an account."""
    return (
        old_balance > 0
        and new_balance == 0
        and amount >= old_balance
    )


def ranking_score(
    strategy,
    transaction_type,
    amount,
    old_balance,
    new_balance,
):
    """Return a ranking score using observable transaction fields."""

    drained = int(
        account_draining(amount, old_balance, new_balance)
    )

    transfer = int(transaction_type == "TRANSFER")

    if strategy == "amount_only":
        return (amount,)

    if strategy == "draining_amount":
        return (
            drained,
            amount,
        )

    if strategy == "draining_transfer_amount":
        return (
            drained,
            transfer,
            amount,
        )

    if strategy == "draining_small_balance":
        # Test whether smaller account balances provide a
        # better secondary priority than large amounts.
        return (
            drained,
            -old_balance,
            amount,
        )

    raise ValueError(f"Unknown strategy: {strategy}")


def make_queue():
    return {
        strategy: []
        for strategy in STRATEGIES
    }


def update_queue(queue, candidate):
    """Keep the highest-ranked REVIEW_CAPACITY transactions."""

    if len(queue) < REVIEW_CAPACITY:
        heapq.heappush(queue, candidate)

    elif candidate > queue[0]:
        heapq.heapreplace(queue, candidate)


def evaluate_queue(queue, total_fraud):
    """Calculate fraud detection metrics after ranking."""

    reviewed = len(queue)

    fraud_captured = sum(
        item[2] for item in queue
    )

    precision = (
        fraud_captured / reviewed
        if reviewed else 0
    )

    capture_rate = (
        fraud_captured / total_fraud
        if total_fraud else 0
    )

    return {
        "reviewed": reviewed,
        "fraud_captured": fraud_captured,
        "precision": precision,
        "capture_rate": capture_rate,
    }


def print_results(period_name, queues, total_fraud):
    print(f"\n===== {period_name} =====")

    print(f"Fraud labels in period: {total_fraud:,}")
    print(f"Review capacity per strategy: {REVIEW_CAPACITY:,}")

    print(
        f"\n{'Strategy':<30}"
        f"{'Captured':>12}"
        f"{'Precision':>14}"
        f"{'Capture rate':>16}"
    )

    print("-" * 72)

    results = {}

    for strategy in STRATEGIES:
        metrics = evaluate_queue(
            queues[strategy],
            total_fraud,
        )

        results[strategy] = metrics

        print(
            f"{strategy:<30}"
            f"{metrics['fraud_captured']:>12,}"
            f"{metrics['precision']:>13.2%}"
            f"{metrics['capture_rate']:>15.2%}"
        )

    return results


def main():
    if not DATA_PATH.is_file():
        raise FileNotFoundError(
            f"Missing PaySim dataset: {DATA_PATH}"
        )

    # Pass 1: determine the chronological split.
    # PaySim's "step" represents simulated hourly time steps.
    step_counts = Counter()

    with DATA_PATH.open(
        "r", newline="", encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            step_counts[int(row["step"])] += 1

    total_transactions = sum(step_counts.values())

    target_train_count = int(
        total_transactions * TRAIN_FRACTION
    )

    cumulative = 0
    split_step = None

    for step in sorted(step_counts):
        cumulative += step_counts[step]

        if cumulative >= target_train_count:
            split_step = step
            break

    if split_step is None:
        raise ValueError("Unable to determine chronological split")

    development_queues = make_queue()
    holdout_queues = make_queue()

    development_transactions = 0
    holdout_transactions = 0

    development_fraud = 0
    holdout_fraud = 0

    draining_counts = Counter()
    draining_fraud_counts = Counter()

    # Pass 2: evaluate ranking strategies.
    with DATA_PATH.open(
        "r", newline="", encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row_number, row in enumerate(reader, start=1):
            step = int(row["step"])
            actual_fraud = int(row["isFraud"])

            is_development = step <= split_step

            if is_development:
                development_transactions += 1
                development_fraud += actual_fraud
                queues = development_queues

            else:
                holdout_transactions += 1
                holdout_fraud += actual_fraud
                queues = holdout_queues

            transaction_type = row["type"]

            # The investigation pool is limited to outgoing
            # TRANSFER and CASH_OUT transactions.
            if transaction_type not in (
                "TRANSFER",
                "CASH_OUT",
            ):
                continue

            amount = float(row["amount"])
            old_balance = float(row["oldbalanceOrg"])
            new_balance = float(row["newbalanceOrig"])

            drained = account_draining(
                amount,
                old_balance,
                new_balance,
            )

            if drained:
                draining_counts[transaction_type] += 1
                draining_fraud_counts[
                    transaction_type
                ] += actual_fraud

            for strategy in STRATEGIES:
                score = ranking_score(
                    strategy,
                    transaction_type,
                    amount,
                    old_balance,
                    new_balance,
                )

                # Fraud label is payload only.
                # Unique row order resolves score ties before
                # Python can compare the fraud label.
                candidate = (
                    score,
                    -row_number,
                    actual_fraud,
                    transaction_type,
                    amount,
                )

                update_queue(
                    queues[strategy],
                    candidate,
                )

    print("\n===== PAYSIM DATASET =====")
    print(f"Total transactions: {total_transactions:,}")
    print(f"Chronological split step: {split_step}")
    print(
        f"Development transactions: "
        f"{development_transactions:,}"
    )
    print(
        f"Holdout transactions: "
        f"{holdout_transactions:,}"
    )
    print(
        f"Total fraud labels: "
        f"{development_fraud + holdout_fraud:,}"
    )

    print("\n===== ACCOUNT-DRAINING PROFILE =====")

    for transaction_type in ("TRANSFER", "CASH_OUT"):
        count = draining_counts[transaction_type]
        fraud = draining_fraud_counts[transaction_type]

        rate = fraud / count if count else 0

        print(
            f"{transaction_type}: "
            f"{count:,} candidates, "
            f"{fraud:,} fraud labels, "
            f"{rate:.2%} fraud-label rate"
        )

    development_results = print_results(
        "DEVELOPMENT PERIOD",
        development_queues,
        development_fraud,
    )

    # Select the winning strategy using development data only.
    # Highest captured count wins; listed order resolves ties.
    selected_strategy = max(
        STRATEGIES,
        key=lambda name: development_results[
            name
        ]["fraud_captured"],
    )

    print(
        f"\nSelected strategy from development: "
        f"{selected_strategy}"
    )

    holdout_results = print_results(
        "CHRONOLOGICAL HOLDOUT PERIOD",
        holdout_queues,
        holdout_fraud,
    )

    selected_metrics = holdout_results[
        selected_strategy
    ]

    print("\n===== FINAL HOLDOUT EVALUATION =====")

    print(f"Selected strategy: {selected_strategy}")
    print(
        f"Fraud captured: "
        f"{selected_metrics['fraud_captured']:,}"
    )
    print(
        f"Precision at {REVIEW_CAPACITY:,}: "
        f"{selected_metrics['precision']:.2%}"
    )
    print(
        f"Holdout fraud capture rate: "
        f"{selected_metrics['capture_rate']:.2%}"
    )

    print(
        "\nImportant: PaySim is synthetic. "
        "This is a retrospective evaluation, "
        "not production validation."
    )


if __name__ == "__main__":
    main()
