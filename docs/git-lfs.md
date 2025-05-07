## Introduction

Some large files in this project are tracked using **Git LFS (Large File Storage)**.

Before working with the project, make sure Git LFS is **installed** and **set up** on your system.

### Installation

You can install Git LFS using one of these links:

- [Official Git LFS website](https://git-lfs.com/)
- [GitHub installation guide](https://github.com/git-lfs/git-lfs/blob/main/INSTALLING.md#installing-packages)
- [Arch Linux package](https://archlinux.org/packages/extra/x86_64/git-lfs/)

### Set up Git LFS hooks

Run this command to set up Git LFS hooks:

```bash
git lfs install
````

> [!CAUTION]
> **Important:** If you are using custom Git hooks with `core.hooksPath`, you must also add the Git LFS hooks there. <br>
> See [this comment](https://github.com/git-lfs/git-lfs/issues/2865#issuecomment-1793219510) for details. <br>
> Make sure to include all the hooks listed in `git lfs install --manual`. <br>
> Example: `pre-push`, `post-checkout`, `post-commit`, `post-merge`
