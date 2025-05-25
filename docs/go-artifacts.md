# Artifact Repository

https://github.com/IFRCGo/go-api-artifacts

## What is this?

This is a **GitHub repository** used to store and manage **build files**, **generated files**, or **automation results** made by other tools or workflows (like GitHub Actions or CI/CD pipelines).

- Why use this?
  - Keeps the main source code clean by storing big or auto-made files separately.
  - Other projects (like go-web-app) can download the required files as required.

## Creating PAT token

- Token name: **ifrc-go-artifacts**
- Resource owner: **IFRCGO**
- Expiration: **No expiration**
- Repository access: **Only select repositories**
  - Repository: **IFRCGo/go-api-artifacts**
- Permissions:
  - Repository permissions
    - Contents: **Read and write**
