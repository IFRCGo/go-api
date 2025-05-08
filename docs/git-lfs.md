## Introduction

This project uses **Git LFS (Large File Storage)** to track some large files.

Before working on the project, make sure Git LFS is **installed** and **set up** on your system.

## Installation

You can install Git LFS from one of these sources:

- [Official Git LFS website](https://git-lfs.com/)
- [GitHub installation guide](https://github.com/git-lfs/git-lfs/blob/main/INSTALLING.md#installing-packages)
- [Arch Linux package](https://archlinux.org/packages/extra/x86_64/git-lfs/)

## Set Up Git LFS Hooks

Run this command to set up Git LFS hooks:

```bash
git lfs install
````

> [!TIP]
> If you use custom Git hooks with `core.hooksPath`, you must also add the Git LFS hooks there. <br>
> See [this comment](https://github.com/git-lfs/git-lfs/issues/2865#issuecomment-1793219510) for work around. <br>
> Be sure to include all the hooks listed in `git lfs install --manual`, like `pre-push`, `post-checkout`, `post-commit`, and `post-merge`.

## View Tracked Files

To see which files are tracked by Git LFS:

```bash
git lfs track
```

## Add New Files to Git LFS

Git LFS uses a `.gitattributes` file to track changes. You also need to commit this file.

```bash
# Track a single file
git lfs track openapi-schema.yaml

# Track multiple files — use quotes to avoid shell expansion
git lfs track "*.bin"
```
> [!TIP]
> Detail tutorial here: https://github.com/git-lfs/git-lfs/wiki/Tutorial

> [!CAUTION]
> Git LFS has usage limits. **High usage** may lead to extra charges and cause interruptions. <br>
>
> Included bandwidth: https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-git-large-file-storage/about-billing-for-git-large-file-storage#included-bandwidth-and-storage-per-month
>
> Pricing: https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-git-large-file-storage/about-billing-for-git-large-file-storage#pricing-for-paid-usage
