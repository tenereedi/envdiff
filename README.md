# envdiff

> Diff and reconcile `.env` files across environments with secret masking.

---

## Installation

```bash
pip install envdiff
```

Or install from source:

```bash
pip install git+https://github.com/yourname/envdiff.git
```

---

## Usage

Compare two `.env` files and mask sensitive values:

```bash
envdiff .env.development .env.production
```

**Example output:**

```
KEY                  development       production
─────────────────────────────────────────────────
DATABASE_URL         ****              ****
DEBUG                true              false
NEW_RELIC_KEY        [missing]         ****
LOG_LEVEL            debug             info
```

Reconcile missing keys interactively:

```bash
envdiff --reconcile .env.development .env.production
```

Export a merged result:

```bash
envdiff --merge .env.development .env.production -o .env.merged
```

Disable secret masking (show raw values):

```bash
envdiff --no-mask .env.staging .env.production
```

---

## Options

| Flag | Description |
|------|-------------|
| `--reconcile` | Interactively fill in missing keys |
| `--merge` | Merge files and write output |
| `-o, --output` | Output file path |
| `--no-mask` | Disable masking of secret values |

---

## License

MIT © 2024 [yourname](https://github.com/yourname)