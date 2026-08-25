# PyRepec

[![PyPI downloads](https://img.shields.io/pypi/dm/pyrepec)](https://pypi.org/project/pyrepec/)
[![Python versions](https://img.shields.io/pypi/pyversions/pyrepec)](https://pypi.org/project/pyrepec/)

PyRepec is a small Python client for the [RePEc API](https://ideas.repec.org/api.html).
It provides typed result models, basic in-session caching, and helpers for querying
authors, publications, bibliographic references, and JEL codes.

Current Version: 0.2.4

## Requirements

- Python 3.9 or newer
- A RePEc API token

## Installation

Install the package from PyPI:

```bash
pip install pyrepec
```

## Quick start

Keep the API token outside your source code, for example in the
`REPEC_TOKEN` environment variable:

```bash
export REPEC_TOKEN="your-token"
```

Create a client and perform a request:

```python
import os

from pyrepec import Repec

repec = Repec(os.environ["REPEC_TOKEN"])
result = repec.get_org_authors("RePEc:edi:bdigvit")

if result.error is not None:
    print(f"RePEc error {result.error.code}: {result.error.message}")
else:
    for author in result.data:
        print(author)
```

Successful responses expose their payload through `result.data`. Errors reported
by RePEc are available through `result.error`; in that case, `result.data` is
empty. HTTP errors are raised by `requests` in the usual way.

## Available methods

| Method | Description | Result type |
| --- | --- | --- |
| `get_org_authors(org_id)` | Get the authors associated with an organization. | `RepecResultList` |
| `get_author_data(author_id)` | Get the full record for an author. | `RepecSingleResult` |
| `get_authors_for_item(item_id)` | Get the authors of a paper or article. | `RepecResultList` |
| `get_jel_codes(item_id)` | Get the JEL codes associated with an item. | `RepecJelResult` |
| `get_ref(item_id)` | Get the bibliographic references for an item. | `RepecSingleResult` |
| `get_error(err_code)` | Resolve a RePEc error code into its function and description. | `tuple[str, str]` |

The exact dictionaries returned in `data` follow the upstream RePEc API response
format.

## Development

Clone the repository and install the locked development environment:

```bash
git clone https://github.com/andrea-cap/pyrepec.git
cd pyrepec
uv sync --locked
```

Run the test suite and code-quality checks:

```bash
uv run pytest ./tests/
uv run ruff check .
uv run ruff format --check .
```

Integration tests require `REPEC_TOKEN`; without it, they are skipped. Unit tests
do not make external API calls.

Generate the changelog from the available Git history:

```bash
uv run gitchangelog
```

## Reporting issues

Report bugs and request features through the
[GitHub issue tracker](https://github.com/andrea-cap/pyrepec/issues).
