# Tests

Backend tests (pytest) live in [`backend/tests/`](../backend/tests/) — run with:

```bash
cd backend && pytest tests/ -v
```

This top-level `tests/` directory is reserved for future end-to-end / cross-service tests
(e.g. a Playwright suite driving the running frontend against the running backend).
