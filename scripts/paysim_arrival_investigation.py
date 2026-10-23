"""Hourly PaySim fraud-review simulation with a 24-hour investigation window.

Usage: python scripts/paysim_arrival_investigation.py

Transactions are synthetic. Reviews are simulated and are not fraud prevention.
The 24-hour SLA, 24-hour staffing and 1,000/day capacity are assumptions.
"""
import csv
import heapq
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / 'data' / 'external' / 'PS_20174392719_1491204439457_log.csv'
HOURS_PER_DAY = 24
DAILY_CAPACITY = 1000
SLA_HOURS = 24
SPLIT_STEP = 323
STRATEGIES = ('amount_only', 'draining_amount')


def day_of(step):
    return (step - 1) // HOURS_PER_DAY + 1


def period_of(step):
    # Classify each transaction by its arrival step, not its review step.
    if step <= SPLIT_STEP:
        return 'development'
    return 'holdout'


def hourly_slots(step):
    hour = (step - 1) % HOURS_PER_DAY
    return DAILY_CAPACITY // HOURS_PER_DAY + (hour < DAILY_CAPACITY % HOURS_PER_DAY)


def fresh_metrics():
    return defaultdict(int)


def state():
    return {
        'priority': [],  # (-drain, -amount, arrival_row, alert_id)
        'expiry': [],    # (expiry_step, alert_id)
        'pending': {},   # id -> (arrival_step, fraud_label, arrival_period)
        'metrics': defaultdict(fresh_metrics),
        'daily': defaultdict(fresh_metrics),
        'waits': defaultdict(list),
    }


def drain_flag(row, amount):
    old = float(row['oldbalanceOrg'])
    new = float(row['newbalanceOrig'])
    return old > 0 and new == 0 and amount >= old

def add_alert(st, strategy, alert_id, step, amount, drained, fraud):
    # The label is stored for retrospective evaluation only, never in the score.
    period = period_of(step)
    st['pending'][alert_id] = (step, fraud, period)
    if strategy == 'amount_only':
        priority = (-amount, alert_id, alert_id)
    else:
        priority = (-int(drained), -amount, alert_id, alert_id)
    heapq.heappush(st['priority'], priority)
    # An alert arriving in step t is eligible for reviews in steps t..t+23.
    heapq.heappush(st['expiry'], (step + SLA_HOURS, alert_id))


def expire_alerts(st, step):
    while st['expiry'] and st['expiry'][0][0] <= step:
        _, alert_id = heapq.heappop(st['expiry'])
        alert = st['pending'].pop(alert_id, None)
        if alert is None:
            continue
        arrival, fraud, period = alert
        st['metrics'][period]['expired'] += 1
        st['metrics'][period]['expired_fraud'] += fraud
        st['daily'][day_of(arrival)]['expired'] += 1
        st['daily'][day_of(arrival)]['expired_fraud'] += fraud


def review_hour(st, step):
    expire_alerts(st, step)
    slots = hourly_slots(step)
    review_day = day_of(step)
    st['daily'][review_day]['capacity_slots'] += slots
    count = 0
    while count < slots and st['priority']:
        *_, alert_id = heapq.heappop(st['priority'])
        alert = st['pending'].pop(alert_id, None)
        if alert is None:  # already expired or reviewed
            continue
        arrival, fraud, period = alert
        wait_hours = step - arrival
        if not 0 <= wait_hours < SLA_HOURS:
            raise AssertionError('Review occurred outside SLA')
        st['metrics'][period]['reviewed'] += 1
        st['metrics'][period]['captured'] += fraud
        st['daily'][review_day]['reviews_performed'] += 1
        st['daily'][day_of(arrival)]['cohort_reviewed'] += 1
        st['daily'][day_of(arrival)]['cohort_captured'] += fraud
        st['waits'][period].append(wait_hours)
        count += 1

def main():
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f'PaySim CSV not found: {DATA_PATH}')

    states = {name: state() for name in STRATEGIES}
    arrivals = defaultdict(fresh_metrics)
    daily_arrivals = defaultdict(fresh_metrics)
    current_step = None
    total_rows = 0
    last_step = 0

    with DATA_PATH.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        required = {'step', 'type', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 'isFraud'}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f'Missing CSV columns: {sorted(required - set(reader.fieldnames or []))}')
        for total_rows, row in enumerate(reader, start=1):
            step = int(row['step'])
            if step < 1 or (current_step is not None and step < current_step):
                raise ValueError('CSV must be sorted in nondecreasing positive step order')
            if current_step is None:
                current_step = step
            if step != current_step:
                for hour in range(current_step, step):
                    for st in states.values():
                        review_hour(st, hour)
                current_step = step
            last_step = step
            fraud = int(row['isFraud'])
            if fraud not in (0, 1):
                raise ValueError(f'Unexpected fraud label at row {total_rows}')
            period = period_of(step)
            arrivals[period]['all_transactions'] += 1
            arrivals[period]['all_fraud'] += fraud
            if row['type'] not in ('TRANSFER', 'CASH_OUT'):
                continue
            arrivals[period]['eligible'] += 1
            arrivals[period]['eligible_fraud'] += fraud
            daily_arrivals[day_of(step)]['eligible'] += 1
            daily_arrivals[day_of(step)]['eligible_fraud'] += fraud
            amount = float(row['amount'])
            drained = drain_flag(row, amount)
            for name, st in states.items():
                add_alert(st, name, total_rows, step, amount, drained, fraud)

    if current_step is None:
        raise ValueError('No transactions in CSV')

    # Finish all arrivals' 24-hour review windows. These extra simulated
    # hours have no new transactions and may use review capacity.
    for hour in range(current_step, last_step + SLA_HOURS):
        for st in states.values():
            review_hour(st, hour)

    print('=== ARRIVAL-COHORT FRAUD INVESTIGATION ===')
    print(f'Rows: {total_rows:,} | Last arrival step: {last_step}')
    print(f'Capacity: {DAILY_CAPACITY}/day | SLA: {SLA_HOURS} hourly steps')
    print('Holdout boundary: step 323 (arrival cohort; split day included by step)')
    print('All arrivals get their complete 24-hour review window.')

    for period in ('development', 'holdout'):
        source = arrivals[period]
        print(f'\n=== {period.upper()} ARRIVAL COHORT ===')
        print(f"All transactions: {source['all_transactions']:,}; "
              f"eligible: {source['eligible']:,}; "
              f"eligible fraud: {source['eligible_fraud']:,}; "
              f"all fraud: {source['all_fraud']:,}")
        for name, st in states.items():
            m = st['metrics'][period]
            eligible = source['eligible']
            eligible_fraud = source['eligible_fraud']
            reviewed = m['reviewed']
            captured = m['captured']
            expired = m['expired']
            waits = st['waits'][period]
            avg_wait = sum(waits) / len(waits) if waits else 0
            print(f'{name}: reviewed={reviewed:,}, captured={captured:,}, '
                  f'precision={captured/reviewed:.2%} ' if reviewed else f'{name}: reviewed=0, captured=0, precision=N/A ', end='')
            print(f'cohort_capture={captured/eligible_fraud:.2%} ' if eligible_fraud else 'cohort_capture=N/A ', end='')
            print(f'expired={expired:,}, expired_fraud={m["expired_fraud"]:,}, '
                  f'avg_wait_hours={avg_wait:.2f}')
            if reviewed + expired != eligible or captured + m['expired_fraud'] != eligible_fraud:
                raise AssertionError(f'Unreconciled arrival cohort: {period} / {name}')
        diff = states['draining_amount']['metrics'][period]['captured'] - states['amount_only']['metrics'][period]['captured']
        print(f'Additional fraud labels reviewed by draining_amount: {diff:+,}')

        print('\n=== REVIEW CAPACITY UTILIZATION (ALL HOURS, INCLUDING DRAIN) ===')
    for name, st in states.items():
        slots = sum(m['capacity_slots'] for m in st['daily'].values())
        performed = sum(m['reviews_performed'] for m in st['daily'].values())
        print(f'{name}: {performed:,}/{slots:,} slots ({performed/slots:.2%})')
        if st['pending']:
            raise AssertionError(f'Unresolved alerts remain for {name}: {len(st["pending"])}')

    print('\n=== INTERPRETATION NOTES ===')
    print('Reviews are label-matched synthetic investigations, not prevented fraud.')
    print('Review occurs after all transactions for that hour arrive; within-hour timing is unknown.')
    print('24-hour expiry, 24/7 staffing and capacity are hypothetical assumptions.')
    print('Development/holdout are classified by arrival step, not review time.')
    print('The holdout has been examined in prior experiments; results are exploratory.')
    print('PaySim draining signals may reflect synthetic generator mechanics.')


if __name__ == '__main__':
    main()
