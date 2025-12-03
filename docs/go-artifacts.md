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

## Submodule Pointer Workflow

Keep CI green by ensuring the parent repo points to a submodule commit that exists on the remote.

- Update submodule content and push:
  ```bash
  cd assets
  git checkout -b update-artifacts
  # make changes (e.g., regenerate schema)
  git add -A
  git commit -m "Update artifacts"
  git push origin update-artifacts
  # open PR in IFRCGo/go-api-artifacts and merge to main
  git checkout main && git pull
  cd -
  ```
- Record new submodule commit in parent:
  ```bash
  # ensure the submodule worktree is on the merged commit
  cd assets && git checkout main && git pull && cd -
  git add assets
  git commit -m "Update assets submodule pointer"
  git push origin <your-go-api-branch>
  ```
- GitHub Actions checkout settings (recommended):
  ```yaml
  - uses: actions/checkout@v4
    with:
      fetch-depth: 0
      submodules: recursive
  ```

Notes
- Avoid amending/rebasing submodule commits that the parent already references; make a new commit instead.
- Ensure submodule commit is on `origin/main` (or a ref CI can fetch) before updating the parent pointer.

## Submodule Commands Cheat Sheet

Common commands you’ll use with `assets` submodule:

- Initialize submodules after clone:
  ```bash
  git submodule update --init --recursive
  ```
- Sync `.gitmodules` config to local submodule metadata:
  ```bash
  git submodule sync
  ```
- Move submodule to latest commit from its remote tracking branch:
  ```bash
  git submodule update --remote assets
  git add assets
  git commit -m "Sync assets to latest remote commit"
  ```
- Pin submodule to a specific commit (e.g., after checkout):
  ```bash
  cd assets
  git checkout <commit-or-branch>
  cd -
  git add assets
  git commit -m "Update assets submodule pointer"
  ```
- Switch submodule remote to SSH (avoid HTTPS prompts):
  ```bash
  git config -f .gitmodules submodule.assets.url git@github.com:IFRCGo/go-api-artifacts.git
  git submodule sync
  cd assets && git remote set-url origin git@github.com:IFRCGo/go-api-artifacts.git && cd -
  git add .gitmodules assets
  git commit -m "Use SSH for artifacts submodule"
  ```
