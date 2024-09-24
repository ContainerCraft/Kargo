# Contributing to Kargo

First off, thank you for your interest in Kargo! The Kargo project is designed to provide a delightful Developer Experience (DX) and User Experience (UX), and we welcome contributions from the community to help continue this mission. Whether you're fixing a bug, adding a new feature, or improving documentation, your contributions are greatly appreciated.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Setting up Development Environment](#setting-up-development-environment)
3. [How to Contribute](#how-to-contribute)
   - [Reporting Bugs](#reporting-bugs)
   - [Suggesting Enhancements](#suggesting-enhancements)
   - [Submitting Changes](#submitting-changes)
4. [Style Guides](#style-guides)
   - [Python Style Guide](#python-style-guide)
   - [Commit Messages](#commit-messages)
   - [Documentation](#documentation)
5. [Testing](#testing)
6. [Continuous Integration](#continuous-integration)
7. [Communication](#communication)
8. [Acknowledgements](#acknowledgements)
9. [Additional Resources](#additional-resources)

---

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [emcee@braincraft.io](mailto:emcee@braincraft.io).

---

## Getting Started

### Prerequisites

- **Github Account**:
- **Docker / Docker Desktop**:
- **VSCode**:
- **VSCode | Devcontainer Extension**:

### Setting up Development Environment

1. **Fork the Repository**:
   - Navigate to the [Kargo GitHub repository](https://github.com/your-org/kargo) and click "Fork".

2. **Clone the Forked Repository**:
   ```sh
   git clone https://github.com/your-username/kargo.git
   cd kargo
   ```

3. **Launch VSCode**:

  > NOTE: When prompted, relaunch in devcontainer wich will supply all dependencies.

   ```sh
   code .
   ```

4. **Login & Install Dependencies**:
   ```sh
   pulumi login
   pulumi install
   ```

5. **Configure Pre-commit Hooks**:
   ```sh
   pip install pre-commit
   pre-commit install
   ```

---

## How to Contribute

### Reporting Bugs

If you've found a bug, please open an issue on GitHub. Fill out the provided template with as much detail as possible, including:
- The version of Kargo you're using
- Steps to reproduce the bug
- Any relevant logs or screenshots

### Suggesting Enhancements

To suggest an enhancement, please open an issue with the "enhancement" label. Provide a clear description of the improvement and why it would be beneficial for the project.

### Submitting Changes

1. **Create a Branch**:
   ```sh
   git checkout -b feature/user/my-new-feature
   ```

2. **Make Your Changes**:
   - Ensure your code adheres to the [Python Style Guide](#python-style-guide).
   - Write tests to cover your changes.

3. **Commit Your Changes**:
   ```sh
   git add .
   git commit -m "feat: add new feature"
   ```

4. **Push to Your Fork**:
   ```sh
   git push origin user/feature/my-new-feature
   ```

5. **Open a Pull Request**:
   - Navigate to the repository on GitHub and click "Compare & pull request". Fill in the template and submit.

---

## Style Guides

### Python Style Guide

Adhere to [PEP 8](https://www.python.org/dev/peps/pep-0008/) and aim for clean, readable code. We recommend using `flake8` and `black` to maintain code quality:
```sh
pip install flake8 black
flake8 .
black .
```

### Commit Messages

- Follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.
- Example Commit Message:
  ```
  feat: add support for Kubernetes 1.24

  This commit adds compatibility with Kubernetes 1.24, ensuring all API changes are accommodated.
  ```

### Documentation

- Use clear and concise docstrings for functions and classes.
- Update `README.md` and other relevant documentation files as applicable.

---

## Testing

1. **Unit Tests**: Your code should be accompanied by unit tests to ensure robust coverage.
2. **Running Tests**:
   ```sh
   pytest
   ```

---

## Continuous Integration

We use GitHub Actions for CI/CD. All pull requests will be automatically tested. Please ensure your PR passes all checks before requesting a review.

---

## Communication

- **GitHub Issues**: For proposing features, reporting bugs, and suggesting improvements.
- **Email**: For sensitive or private communication, please contact [emcee@braincraft.io](mailto:emcee@braincraft.io).

---

## Acknowledgements

Thank you to all the contributors who make this project possible. Your time and effort are sincerely appreciated!

---

## Additional Resources

- [Pulumi Documentation](https://www.pulumi.com/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

Thank you for contributing to Kargo!
