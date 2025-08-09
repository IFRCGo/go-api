# Artifact Repository

https://github.com/IFRCGo/go-api-artifacts

## What is this?

This is a **GitHub repository** used to store and manage **build files**, **generated files**, or **automation results** made by other tools or workflows (like GitHub Actions or CI/CD pipelines).

- Why use this?
  - Keeps the main source code clean by storing big or auto-made files separately.
  - Other projects (like go-web-app) can download the required files as required.

## Creating a PAT Token

A GitHub PAT (Personal Access Token) is needed to upload files to the `go-api-artifacts` repository.
This token is stored in the GitHub Actions secret: `secrets.GO_API_ARTIFACTS_TOKEN`.
For more details, see [ci.yml](/.github/workflows/ci.yml).

> [!Important]
> Currently, the PAT token is created using the https://github.com/ifrcgo-dev account.

### How to create a new token:

- **Go to**: [GitHub Personal Access Tokens](https://github.com/settings/personal-access-tokens)
- **Token name**: `ifrc-go-artifacts-xyz` (replace `xyz` as needed)
- **Resource owner**: `IFRCGO`
- **Expiration**: No expiration
- **Repository access**: Only select repositories
  - Select: `IFRCGo/go-api-artifacts`
- **Permissions**:
  - **Repository permissions**:
    - **Contents**: Read and write
