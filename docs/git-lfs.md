## Introduction

Few large files are tracked in Git using Git LFS (Large File Storage).

Before working with it, make sure Git LFS is installed and configured on your system.

### Installation

You can install Git LFS using one of these resources:

- [Official Git LFS website](https://git-lfs.com/)
- [GitHub installation guide](https://github.com/git-lfs/git-lfs/blob/main/INSTALLING.md#installing-packages)
- [Arch Linux package](https://archlinux.org/packages/extra/x86_64/git-lfs/)

### Set up Git LFS hooks

Run the following command to set up Git LFS:

```bash
git lfs install
````
> [!TIP]
> **Note:** If you're using custom Git hooks with `core.hooksPath`, make sure to include the Git LFS hooks as well.
> [More details here](https://github.com/git-lfs/git-lfs/issues/2865#issuecomment-1793219510)
