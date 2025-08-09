# Development Philosophy & Craftsmanship

This document outlines the core principles that guide all development within the `hoopstat-haus` project. As an AI contributor, you are expected to understand and adhere to these principles in all generated code, commits, and pull requests.

Our guiding star is a quote from the essay [*Programming Sucks*](https://www.stilldrinking.org/programming-sucks): **"All code is bad"**

We write efficient, clear, maintainable code to be kind to our future selves and collaborators.

---

## 1. Code is for Humans First

Code's primary audience is not the computer, but the human developers who will read, debug, and maintain it.

* **Clarity Over Cleverness:** The code must be simple, readable, and easy to understand. Avoid obscure language features or overly complex one-liners.
* **Meaningful Naming:** Variables, functions, and classes must have descriptive names that reveal their intent.
* **Comments Explain *Why*, Not *What*:** Use comments to explain complex logic or the reasoning behind a design decision, not to state what the code is obviously doing.

---

## 2. Favor Simplicity & Static-First Design

Complexity is the primary enemy of sustainable software. We aggressively pursue simplicity and seek to minimize moving parts wherever possible.

* **Static Over Dynamic:** We prefer static, build-time solutions over dynamic, run-time ones. This reduces the cognitive load and potential for run-time errors.
* **YAGNI (You Ain't Gonna Need It):** Do not implement features or add abstractions for speculative future use cases. Solve the problem at hand and no more.
* **Code is a Liability:** Every line of code adds to the project's maintenance burden. The goal is to solve the problem with the least amount of code possible.

---

## 3. The `main` Branch is Sacred

The `main` branch is the source of truth and must always be in a deployable state. Its integrity is paramount.

* **Always Deployable:** A commit to `main` means it is tested, reviewed, and ready for production.
* **Fix-Forward, Never Rewind:** The history of the `main` branch must never be rewritten. There are no `force-pushes`. If a mistake is made, it will be corrected with a new commit or a revert, preserving the historical record.
* **PRs are the Only Gateway:** All new commits arrive on `main` through Pull Requests that have passed all required automated checks and a human review.

---

## 4. Confidence Through Automated Testing

Automated tests are the non-negotiable foundation of our confidence. They are what allow us to refactor and build new features without fear.

* **Test What Matters:** We are not dogmatic about the *type* of tests (unit, integration, E2E, etc.). What is critical is that key functionality is covered by some form of reliable, automated testing.
* **Tests as Living Documentation:** Well-written tests should clearly demonstrate how a piece of code is intended to be used and are often the best form of documentation.
* **Coverage is a Goal, Not a Dogma:** We aim for good test coverage but focus on testing critical paths and complex logic rather than chasing a meaningless 100% metric.

---

## 5. Leave the Code Better Than You Found It

We embrace the "Boy Scout Rule." Any time you touch a file, you are responsible for leaving it in a better state.

* **Incremental Refactoring:** If you encounter unclear code or a minor issue while working on a task, clean it up as part of your work.
* **Address Technical Debt:** Do not introduce new technical debt. If existing debt must be addressed to complete your task, do so in a separate, clearly labeled commit.

---

## 6. Commit Hygiene is Non-Negotiable

A clean commit history is a readable story of the project's evolution.

* **Atomic Commits:** Each commit on `main` must represent a single, logical change. Iterative progress commits are fine on branches, but should be squashed into a single "mergeable" commit before or during PR review.
* **Descriptive Commit Messages:** Follow the conventional commit message format. The subject line should be a short, imperative summary, and the body should provide context.
