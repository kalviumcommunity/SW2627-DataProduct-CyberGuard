# CyberGuard Development Workflow

## Branching Strategy

- main contains production-ready code.
- Every new task is developed in a feature branch.
- Branch naming:
  - feature/<description>
  - fix/<description>
  - docs/<description>
  - refactor/<description>
  - chore/<description>
- Branches are deleted after merge.

---

## Commit Convention

Format

[type]: description

Examples

feat: implement authentication pipeline

fix: correct failed login calculation

docs: update dashboard documentation

refactor: simplify risk scoring logic

chore: update dependencies

This convention provides a clean Git history and supports changelog generation.

---

## Pull Request Process

Every PR must:

- Link to related GitHub Issue
- Describe changes
- Pass GitHub Actions
- Receive at least one approval
- Be reviewed for:
  - correctness
  - readability
  - data integrity
  - testing

---

## Issue Tracking

Every feature begins with a GitHub Issue.

Issues include:

- title
- description
- label
- assignee

Issues are closed only after the related Pull Request is merged.