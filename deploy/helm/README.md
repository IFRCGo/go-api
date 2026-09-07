# ifrcgo-helm

Helm chart to deploy the IFRC GO API. A thin wrapper around the shared `banjo-helm` application chart (aliased as `app`), so **every value nests under `app:`** — the only value of our own is the `playwright:` block. Keys the subchart accepts:

```bash
helm show values oci://ghcr.io/toggle-corp/banjo-helm --version "$(yq '.dependencies[0].version' Chart.yaml)"
```

CI publishes the chart to a registry; what deploys it is an ArgoCD Application per cluster in [go-deploy](https://github.com/IFRCGo/go-deploy) (e.g. [`applications/argocd/staging/applications/go-api.yaml`](https://github.com/IFRCGo/go-deploy/blob/develop/applications/argocd/staging/applications/go-api.yaml)), which pins the chart version and picks the value files below. Publishing a version and rolling it out to a cluster is [`docs/go-deploy.md`](../../docs/go-deploy.md).

## Layout

- `values.yaml` — shared base: web (`api`), Celery `worker`, pre-deploy `hooks` (wait-for-resources / db-migrate / collect-static), `cronjobs`, `playwright`.
- `values/operators/` — one file per dependency this deployment provisions itself via an operator, each carrying the custom resource plus the env pointing the app at it: [`dragonfly.yaml`](values/operators/dragonfly.yaml) (Redis broker + cache), [`elasticsearch.yaml`](values/operators/elasticsearch.yaml) (ECK). A deployment using an externally-managed dependency omits the file and supplies the host at deploy time. The operators themselves are installed cluster-wide, outside this chart.
- `values/traefik.yaml` — Traefik ingress class + request-body-size Middleware.
- `values/alpha.yaml` — alpha cluster; no vault, so secrets come from `app.secrets`.
- `values/go-deploy/` — IFRC Azure (AKS) clusters. `base.yaml` holds what they all share (workload identity, TLS ingress, secrets from Azure Key Vault via the Secrets Store CSI driver); apply it first, then exactly one of `sandbox.yaml` / `staging.yaml` / `production.yaml`.
- `templates/playwright.yaml` — the only resource this chart renders itself: the headless browser the screenshot / PDF-export tasks connect to.
- `tests.yaml` / `tests/` / `snapshots/` — snapshot tests.

Domains, credentials, storage account and Sentry DSN are deliberately absent from the repo and supplied per-environment at deploy time; `base.yaml` keeps them as commented-out keys so the set stays visible.

## Deployments

`tests.yaml` is the authoritative list of value files per deployment, in order (`values.yaml` always first; the `tests/*.yaml` entry is a dummy standing in for deploy-time values). `values/traefik.yaml` must come **after** the environment overlay so its `className` wins. Alpha omits `values/operators/elasticsearch.yaml` — it points at an externally-managed Elasticsearch via `ELASTIC_SEARCH_HOST`. Sandbox is not in the snapshot matrix (`values/go-deploy/base.yaml` + `sandbox.yaml`), so its ArgoCD Application is the only record of the rest.

## Configuration

Four sources. The first three are collected into a ConfigMap / Secret and mounted with `envFrom`; `extraEnvVars` becomes a pod-level `env:` entry and therefore **wins over** the other three.

| Key | Rendered as | Use for |
|---|---|---|
| `app.env` | ConfigMap, via `envFrom` | non-secret configuration |
| `app.secrets` | Secret, via `envFrom` — **only when the CSI driver is off** | secrets on a deployment without a vault (alpha) |
| `app.secretsStoreCsiDriver.secretsKeyMap` | SecretProviderClass → synced Secret, via `envFrom` | secrets on the Azure clusters |
| `app.extraEnvVars` | pod `env:` array (supports `valueFrom`) | pointing the app at in-cluster dependencies |

`main/settings.py` lists what the application actually reads. To find every definition:

```bash
rg -A 3 --glob='!{**/tests/**,**/snapshots/**}' 'env:'          deploy/helm
rg -A 3 --glob='!{**/tests/**,**/snapshots/**}' 'extraEnvVars:' deploy/helm
```

`app.env` string values are template-evaluated, so they can reference release data (`GO_ENVIRONMENT: "{{ $.Values.environment }}"`); non-strings are JSON-encoded and quoted; `KEY: null` in an overlay removes an inherited key.

Each `extraEnvVars` dict value is a full k8s env-var spec minus the name, so besides `{value: ...}` it can be `{valueFrom: {secretKeyRef: ...}}` — that is how a credential an operator publishes as its own Secret reaches the app without being copied into this repo.

### `app.secretsStoreCsiDriver.secretsKeyMap` — Azure Key Vault

Only on the go-deploy clusters (`values/go-deploy/base.yaml`). Each entry maps a container env-var name to a secret name in that cluster's vault, e.g. `DJANGO_SECRET_KEY: DJANGO-SECRET-KEY` reads `DJANGO-SECRET-KEY` from the vault and lands it in the pod as `DJANGO_SECRET_KEY`.

- **Only listed keys are synced.** Adding a secret to the vault does nothing until it is added here.
- **A name listed here that the vault does not hold is a hard failure**, not a skipped key: the CSI driver errors while fetching it, the SecretProviderClass volume never mounts, and the pod stays in `ContainerCreating` with a `FailedMount` event naming the missing secret (`kubectl describe pod` to see it). So a rename in the vault has to land before the deploy that references the new name.
- Vault secret names allow only `0-9 a-z A-Z -` ([object naming rules](https://learn.microsoft.com/en-us/azure/key-vault/general/about-keys-secrets-certificates#object-identifiers)) — hence upper-kebab-case vault names against snake-case env names.
- **Changing a vault value needs no redeploy:** the CSI driver refreshes the mount and [Reloader](https://github.com/stakater/reloader) restarts the pods (banjo-helm sets `reloader.stakater.com/auto: "true"` on its Deployments).
- Which vault, and what it holds, is defined in go-deploy terraform: [`base-infrastructure/terraform/app_resources.tf`](https://github.com/IFRCGo/go-deploy/blob/develop/base-infrastructure/terraform/app_resources.tf).

#### Adding a new secret

Each cluster has its own vault, so the value has to be created once per environment. Roll it out one environment at a time:

1. Add the entry to `secretsKeyMap` in [`values/go-deploy/base.yaml`](values/go-deploy/base.yaml) (`ENV_VAR_NAME: ENV-VAR-NAME`), regenerate the snapshots, and merge.
2. Create the secret in the **staging** vault.
3. Deploy to staging.
4. Create the secret in the **production** vault.
5. Deploy to production.

> [!NOTE]
> The deployment sync fails if the secret is missing from that cluster's vault — the CSI driver cannot fetch it, the SecretProviderClass volume never mounts, and the pods stay in `ContainerCreating`. Always create the vault entry before deploying the release that references it.

> [!NOTE]
> The vault secret name may contain only `0-9 a-z A-Z -`, so it is the env-var name in upper-kebab-case: `NEW_API_TOKEN` → `NEW-API-TOKEN`.

## Cronjobs

`app.cronjobs.jobs` is kept in lockstep with the `SentryMonitor` enum in `main/sentry.py` (job key == management command == monitor name). `cron_job_monitor --validate-only` fails if the two drift and CI runs it on every change — update both together.

CronJobs are created in the same deploy stage as the api and worker, after the pre-deploy hooks, so a first-time install cannot fire a scheduled command against an unmigrated database. That defers when a CronJob is *created*, not when an existing one fires: during an upgrade a CronJob left from the previous release can still run the old image while the migration hook is in flight, so migrations must stay compatible with the previous image — the same constraint a rolling api update already has.

## Working on the chart

```bash
cd deploy/helm
helm dependency build .   # fetches banjo-helm into charts/
helm lint .
```

A bare `helm template -f values.yaml -f values/go-deploy/staging.yaml` cannot render a complete deployment — the ingress host, vault name and other deploy-time values are not in the repo. Render through the snapshot matrix instead, which layers the `tests/*.yaml` dummies on top:

```bash
git submodule update --init   # snapshot tooling lives in fugit/ at the repo root
./update-snapshots.sh         # regenerate; --check-diff-only to only verify
```

Regenerate after any chart change and review the diff — it is the primary review surface for chart edits. CI runs `./update-snapshots.sh --check-diff-only`, so a stale snapshot fails the build.
