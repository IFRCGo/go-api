# Artifact Repository

https://github.com/IFRCGo/go-api-artifacts

## What is this?

This is a **GitHub repository** used to store and manage **build files**, **generated files**, or **automation results**.

- Why use this?
  - Keeps the main source code clean by storing big or auto-made files separately.
  - It helps avoid high costs from Git LFS - See https://github.com/IFRCGo/go-api/pull/2470#issuecomment-2861654878 

> [!Note]
> Previously, GitHub Actions in go-api or related projects uploaded artifacts automatically from CI using a Personal Access Token (PAT).
> Now, CI only checks the current schema against the schema in **go-api-artifacts**.
> **go-api-artifacts** is used as a submodule in **go-api**.

## Developer Workflow

### openapi-schema.yaml
- Generate Schema File locally: 
  - The required artifact files (e.g., `openapi-schema.yaml` file) should be generated in the local clone of the go-api-artifacts repository.
- Commit and Push Schema:
  - The generated files should be pushed to the go-api-artifacts repository.
- Update Submodule Reference:
  - The commit reference should be updated in the main repo.

Command
```bash
docker compose run --rm serve ./manage.py spectacular --file .assets/openapi-schema.yaml
```

### 🚨 Manually added files

- In `go-api-artifacts`
  - For any files **other than `openapi-schema.yaml`**
  - Create a **new branch** in the `go-api-artifacts` repo.
  - Add the files there.
  - Open a **Pull Request in the `go-api-artifacts` repository**.
- In `go-api`
  - **Update the submodule reference** in your `go-api` PR.
  - In the corresponding **`go-api` Pull Request**, include the link to the `go-api-artifacts` PR as a *related PR* so reviewers can track both changes together.
