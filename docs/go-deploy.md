# Deploying go-api

CI publishes the Helm chart and the Docker image; what deploys them is an ArgoCD Application per cluster in [go-deploy](https://github.com/IFRCGo/go-deploy). A release is therefore two steps: **publish a chart version**, then **point the cluster's Application at it**.

For the chart itself (value files per environment, configuration sources, snapshots) see [`deploy/helm/README.md`](../deploy/helm/README.md). For how the clusters are put together, i.e. app-of-apps, Key Vault, workload identities and container registry, see go-deploy's [`applications/argocd/README.md`](https://github.com/IFRCGo/go-deploy/blob/develop/applications/argocd/README.md).

## ArgoCD access

The commands below act on whichever cluster your current kubeconfig context points at; each environment runs its own ArgoCD in the `argocd` namespace.

Admin password:

```bash
kubectl get secret -n argocd argocd-initial-admin-secret --template="{{.data.password}}" | base64 -d
```

Port-forward the UI:

```bash
kubectl port-forward --warnings-as-errors -n argocd svc/argo-cd-argocd-server 8100:80
```

Then open <http://localhost:8100>.

> [!NOTE]
> Use `http`, not `https`. The port-forward targets the server's plaintext port and exits with an error on a TLS handshake.

## 1. Publish a chart version

`develop`, `master` and `project/*` publish automatically on push ([`helm-publish.yaml`](../.github/workflows/helm-publish.yaml)). Any other branch has to be published manually, either from the [workflow page](https://github.com/IFRCGo/go-api/actions/workflows/helm-publish.yaml) or with the [gh CLI](https://cli.github.com/):

```bash
gh workflow run --ref "$(git rev-parse --abbrev-ref HEAD)" .github/workflows/helm-publish.yaml
```

Once the run succeeds, the published chart version and image tag are in the run's summary and annotations.

## 2. Point the cluster at it

Both environments are deployed from go-deploy's `develop` branch. The Application manifests live there, so a chart bump is a commit to that repo.

| Environment | Application manifest | App-of-apps to refresh |
|---|---|---|
| Staging | [`applications/argocd/staging/applications/go-api.yaml`](https://github.com/IFRCGo/go-deploy/blob/develop/applications/argocd/staging/applications/go-api.yaml) | `staging-app-of-apps` |
| Production | [`applications/argocd/production/applications/go-api.yaml`](https://github.com/IFRCGo/go-deploy/blob/develop/applications/argocd/production/applications/go-api.yaml) | `production-app-of-apps` |

1. Set `spec.source.targetRevision` to the chart version published in step 1 and merge to go-deploy `develop`.
2. In ArgoCD, either wait ~3 min for the app-of-apps to poll, or hit **Refresh** on it to trigger the auto-sync immediately.
3. Watch the sync on the `go-api` Application, in the UI or with [k9s](https://k9scli.io/) / `kubectl` from the terminal.

## Key Vault access

Secrets on the IFRC clusters live in a per-application Azure Key Vault and reach the pods through the Secrets Store CSI driver. Background: go-deploy's [Azure KeyVault Managed Secrets](https://github.com/IFRCGo/go-deploy/blob/develop/applications/argocd/README.md#2-azure-keyvault-managed-secrets). Which vault secrets this application reads, and how to add one, is the `secretsKeyMap` section of [`deploy/helm/README.md`](../deploy/helm/README.md#appsecretsstorecsidriversecretskeymap--azure-key-vault).

Reading or editing those secrets needs an admin role on the vault, granted in terraform. Each environment has its own vault and its own state, so the change has to be applied per environment.

1. Get the person's Azure AD user principal (object) ID: `az ad signed-in-user show --query id -o tsv` for your own, or the portal's [Active Directory overview](https://portal.azure.com/#view/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/~/Overview) under *My feed*. Confirm it resolves to the right person by opening `https://portal.azure.com/#view/Microsoft_AAD_UsersAndTenants/UserProfileMenuBlade/~/overview/userId/<user-id>`.
2. In go-deploy [`base-infrastructure/terraform/app_resources.tf`](https://github.com/IFRCGo/go-deploy/blob/develop/base-infrastructure/terraform/app_resources.tf), add the ID to the `user_principal_ids` local at the top of the file if it is not already listed.
3. Add that entry to `vault_admin_ids` on the [`go_api_resources` module](https://github.com/IFRCGo/go-deploy/blob/develop/base-infrastructure/terraform/app_resources.tf#L282):

    ```terraform
    module "go_api_resources" {
      source = "./app_resources"

      app_name = "go-api"
      # ... other config ...

      vault_admin_ids = [
        local.user_principal_ids.tc_navin,
        local.user_principal_ids.<new-person>,
      ]
    }
    ```

4. Apply the terraform against staging and production.

> [!NOTE]
> `vault_admin_ids` wants a **user** ID, not an application or service-principal ID. The workload identity the pods authenticate with is created by the same module and needs no entry here.

> [!NOTE]
> For go-api this module manages only the vault and the workload identity. Its database and blob storage predate it and are administered outside terraform (see the comments on the module).
