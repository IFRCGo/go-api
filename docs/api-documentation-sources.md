# GO API documentation sources

This note clarifies which API documentation sources are **canonical** for IFRCGo/go-api and which legacy pages should be treated as deprecated.

Related: [IFRCGo/go-api#770](https://github.com/IFRCGo/go-api/issues/770), [#2057](https://github.com/IFRCGo/go-api/issues/2057).

## Canonical (maintained)

Use these as the source of truth for API consumers and contributors:

| Source | URL | Purpose |
|--------|-----|---------|
| **Swagger / OpenAPI (production)** | https://goadmin.ifrc.org/docs/ | Interactive API reference for deployed GO API |
| **GO Wiki** | Linked from Swagger and project README | Broader GO platform documentation |
| **Repository README** | [`README.md`](../README.md) | Setup, development, and links to other docs |

When adding or changing endpoints, update OpenAPI schema generation and ensure Swagger reflects the change after deploy.

## Deprecated / legacy

| Source | URL | Status |
|--------|-----|--------|
| **Legacy how-to page** | https://ifrcgo.org/how-to-use-the-go-api/ | **Deprecated** — not cross-linked from canonical docs; content may be stale. Prefer [goadmin.ifrc.org/docs](https://goadmin.ifrc.org/docs/). |

### Recommended action for maintainers

1. Add a banner on the legacy ifrcgo.org page pointing to https://goadmin.ifrc.org/docs/
2. Migrate any unique content from the legacy page into the wiki or Swagger descriptions
3. Remove or redirect the legacy URL when traffic drops

## Contributor checklist

- [ ] New public endpoints documented in OpenAPI / Swagger
- [ ] README links to canonical Swagger URL
- [ ] Do not add new documentation only on legacy ifrcgo.org pages

## In-repo documentation

| Document | Topic |
|----------|-------|
| [`docs/montandon-external-token-jwt.md`](./montandon-external-token-jwt.md) | Montandon / external token JWT flow |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Development setup (when present on default branch) |
