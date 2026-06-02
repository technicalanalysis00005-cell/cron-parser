# cron-parser

Parse and explain cron expressions in human-readable format. Supports standard 5-field cron syntax with step values, ranges, lists, and `@keyword` aliases.

## Features

- **Human-readable explanations** — converts cron syntax to plain English
- **Next run calculator** — shows upcoming scheduled execution times
- **Keyword aliases** — supports `@hourly`, `@daily`, `@weekly`, `@monthly`, `@yearly`
- **Standard cron syntax** — ranges (`1-5`), steps (`*/10`), lists (`1,15,30`)
- **Zero dependencies** — pure Python 3.7+, no external packages

## Installation

```bash
git clone https://github.com/technicalanalysis00005-cell/cron-parser.git
cd cron-parser
```

No dependencies to install — just run it.

## Usage

### Basic explanation

```bash
python cron_parser.py "*/5 * * * *"
```

Output:
```
Expression: */5 * * * *

     */5  →  minute: every 5
       *  →  every hour
       *  →  every day
       *  →  every month
       *  →  every day of week

  Summary: Runs every 5 every minute every hour every day.

  Next 5 scheduled run(s):
    2026-06-02 10:15  (Monday)
    2026-06-02 10:20  (Monday)
    2026-06-02 10:25  (Monday)
    2026-06-02 10:30  (Monday)
    2026-06-02 10:35  (Monday)
```

### Show more upcoming runs

```bash
python cron_parser.py "0 9 * * 1-5" --next 10
```

### Use keyword aliases

```bash
python cron_parser.py "@daily"
python cron_parser.py "@hourly"
python cron_parser.py "@weekly"
```

### Common expressions

| Expression | Description |
|---|---|
| `*/5 * * * *` | Every 5 minutes |
| `0 * * * *` | Every hour |
| `0 9 * * 1-5` | Weekdays at 9:00 AM |
| `0 0 * * *` | Every midnight |
| `30 2 1 * *` | 2:30 AM on the 1st of every month |
| `0 0 1 1 *` | Midnight on January 1st |
| `*/15 9-17 * * 1-5` | Every 15 min during business hours |

## Cron Field Reference

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, Sunday=0)
│ │ │ │ │
* * * * *
```

### Special characters

| Character | Meaning | Example |
|---|---|---|
| `*` | Any value | `*` in minute = every minute |
| `,` | List | `1,3,5` = 1, 3, and 5 |
| `-` | Range | `1-5` = 1, 2, 3, 4, 5 |
| `/` | Step | `*/10` = every 10th value |

## License

MIT
