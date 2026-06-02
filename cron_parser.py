#!/usr/bin/env python3
"""
cron-parser — Parse and explain cron expressions in human-readable format.

Usage:
    python cron_parser.py "*/5 * * * *"
    python cron_parser.py "0 9 * * 1-5" --next 10
    python cron_parser.py "30 2 1 */3 *" --verbose

Supports standard 5-field cron expressions:
    ┌───────────── minute (0-59)
    │ ┌───────────── hour (0-23)
    │ │ ┌───────────── day of month (1-31)
    │ │ │ ┌───────────── month (1-12)
    │ │ │ │ ┌───────────── day of week (0-6, Sunday=0)
    │ │ │ │ │
    * * * * *
"""

import sys
import argparse
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

DAY_NAMES = [
    "Sunday", "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday"
]

FIELD_NAMES = ["minute", "hour", "day of month", "month", "day of week"]
FIELD_RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)]


def parse_field(field: str, low: int, high: int) -> List[int]:
    """Parse a single cron field into a list of valid values."""
    values = set()

    for part in field.split(","):
        # Handle step notation: */N or range/N
        step = 1
        if "/" in part:
            base, step_str = part.split("/", 1)
            step = int(step_str)
            if step <= 0:
                raise ValueError(f"Invalid step value: {step}")
        else:
            base = part

        # Determine range
        if base == "*":
            start, end = low, high
        elif "-" in base:
            start_str, end_str = base.split("-", 1)
            start, end = int(start_str), int(end_str)
            if start > end:
                raise ValueError(f"Invalid range: {start}-{end}")
        else:
            start = end = int(base)

        # Validate bounds
        if start < low or end > high:
            raise ValueError(
                f"Value {start}-{end} out of range {low}-{high}"
            )

        # Generate values
        for v in range(start, end + 1, step):
            values.add(v)

    return sorted(values)


def parse_cron(expr: str) -> Tuple[List[int], ...]:
    """Parse a full 5-field cron expression."""
    parts = expr.strip().split()
    if len(parts) != 5:
        raise ValueError(
            f"Expected 5 fields, got {len(parts)}. "
            f"Format: minute hour day-of-month month day-of-week"
        )

    return tuple(
        parse_field(field, lo, hi)
        for field, (lo, hi) in zip(parts, FIELD_RANGES)
    )


def describe_field(values: List[int], field_index: int) -> str:
    """Generate a human-readable description of a single field."""
    low, high = FIELD_RANGES[field_index]
    full_range = list(range(low, high + 1))

    if values == full_range:
        return "every"

    # Check for step patterns on full range
    if len(values) > 2:
        diffs = [values[i+1] - values[i] for i in range(len(values)-1)]
        if len(set(diffs)) == 1:
            step = diffs[0]
            if values[0] == low:
                return f"every {step}"

    # Check for step patterns starting from offset
    if len(values) > 2:
        diffs = [values[i+1] - values[i] for i in range(len(values)-1)]
        if len(set(diffs)) == 1:
            step = diffs[0]
            return f"every {step} starting at {values[0]}"

    # Format individual values
    if field_index == 3:  # month
        parts = [MONTH_NAMES[v] for v in values]
    elif field_index == 4:  # day of week
        parts = [DAY_NAMES[v] for v in values]
    else:
        parts = [str(v) for v in values]

    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    else:
        return ", ".join(parts[:-1]) + f", and {parts[-1]}"


def explain_cron(expr: str) -> str:
    """Generate a full human-readable explanation of a cron expression."""
    parsed = parse_cron(expr)
    descs = [describe_field(v, i) for i, v in enumerate(parsed)]

    lines = [f"Expression: {expr}", ""]

    # Detailed field breakdown
    for i, (name, values, desc) in enumerate(zip(FIELD_NAMES, parsed, descs)):
        raw = expr.split()[i]
        if desc == "every":
            detail = f"every {name}"
        else:
            detail = f"{name}: {desc}"
        lines.append(f"  {raw:>8}  →  {detail}")

    lines.append("")

    # Natural language summary
    minute, hour, dom, month, dow = descs

    summary_parts = ["Runs"]

    if minute == "every":
        summary_parts.append("every minute")
    else:
        summary_parts.append(f"at minute {minute}")

    if hour == "every":
        if minute != "every":
            summary_parts.append("of every hour")
    else:
        summary_parts.append(f"past hour {hour}")

    if dom == "every":
        if month == "every":
            summary_parts.append("every day")
        else:
            summary_parts.append(f"every day of {month}")
    else:
        summary_parts.append(f"on day {dom}")

    if month != "every":
        summary_parts.append(f"of {month}")

    if dow == "every":
        pass  # no constraint
    else:
        summary_parts.append(f"on {dow}")

    summary = " ".join(summary_parts) + "."
    lines.append(f"  Summary: {summary}")

    return "\n".join(lines)


def next_runs(expr: str, count: int = 5, start: Optional[datetime] = None) -> List[datetime]:
    """Calculate the next N execution times for a cron expression."""
    parsed = parse_cron(expr)
    minutes, hours, doms, months, dows = parsed

    if start is None:
        start = datetime.now().replace(second=0, microsecond=0)
    else:
        start = start.replace(second=0, microsecond=0)

    results = []
    current = start + timedelta(minutes=1)  # Start from next minute
    max_iterations = 366 * 24 * 60  # Safety: up to 1 year
    iterations = 0

    while len(results) < count and iterations < max_iterations:
        iterations += 1

        # Quick skip: if month doesn't match, jump to next valid month
        if current.month not in months:
            # Jump to first valid month
            next_month = None
            for m in sorted(months):
                if m > current.month:
                    next_month = m
                    break
            if next_month is None:
                # Wrap to next year
                current = current.replace(
                    year=current.year + 1,
                    month=sorted(months)[0],
                    day=1, hour=0, minute=0
                )
            else:
                current = current.replace(
                    month=next_month, day=1, hour=0, minute=0
                )
            continue

        # Quick skip: if day of month or day of week doesn't match
        dow_match = current.weekday() in [(d % 7 - 1) % 7 for d in dows]  # Adjust: cron 0=Sun, python 0=Mon
        # Better: use isoweekday or manual mapping
        cron_dow = (current.weekday() + 1) % 7  # Python Mon=0 → Cron Mon=1, Sun=0
        dow_match = cron_dow in dows or 7 in dows  # Handle 7=Sunday alias

        if current.day not in doms or not dow_match:
            current += timedelta(days=1)
            current = current.replace(hour=0, minute=0)
            continue

        if current.hour not in hours:
            next_hour = None
            for h in sorted(hours):
                if h > current.hour:
                    next_hour = h
                    break
            if next_hour is None:
                current += timedelta(days=1)
                current = current.replace(hour=0, minute=0)
            else:
                current = current.replace(hour=next_hour, minute=0)
            continue

        if current.minute not in minutes:
            next_min = None
            for m in sorted(minutes):
                if m > current.minute:
                    next_min = m
                    break
            if next_min is None:
                current += timedelta(hours=1)
                current = current.replace(minute=0)
            else:
                current = current.replace(minute=next_min)
            continue

        # All fields match!
        results.append(current)
        current += timedelta(minutes=1)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Parse and explain cron expressions in human-readable format.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "*/5 * * * *"
  %(prog)s "0 9 * * 1-5" --next 10
  %(prog)s "30 2 1 */3 *" --verbose
  %(prog)s "@hourly"
        """
    )
    parser.add_argument("expression", help="Cron expression (5 fields) or @keyword")
    parser.add_argument(
        "-n", "--next", type=int, default=5, metavar="N",
        help="Show next N scheduled runs (default: 5)"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Show detailed field breakdown"
    )

    args = parser.parse_args()

    # Handle @keywords
    ALIASES = {
        "@yearly":   "0 0 1 1 *",
        "@annually": "0 0 1 1 *",
        "@monthly":  "0 0 1 * *",
        "@weekly":   "0 0 * * 0",
        "@daily":    "0 0 * * *",
        "@midnight": "0 0 * * *",
        "@hourly":   "0 * * * *",
    }

    expr = args.expression.lower().strip()
    if expr in ALIASES:
        print(f"  {args.expression} = {ALIASES[expr]}")
        print()
        expr = ALIASES[expr]

    try:
        # Explanation
        print(explain_cron(expr))
        print()

        # Next runs
        runs = next_runs(expr, args.next)
        if runs:
            print(f"  Next {len(runs)} scheduled run(s):")
            for dt in runs:
                print(f"    {dt.strftime('%Y-%m-%d %H:%M  (%A)')}")
        print()

    except ValueError as e:
        print(f"  Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
