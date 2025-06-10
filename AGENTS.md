
# AGENTS Instructions for NotiPy

These guidelines apply to automated contributions made by language model agents (e.g., ChatGPT, GitHub Copilot).

## 📁 Scope

These rules apply to:
- Automatically translated documentation (e.g., README, docs/ko/)
- Code generated or modified by AI agents

---

## 🧪 Code Quality and Validation

If any `.py` files are modified:

- Run `flake8` or `pylint` for linting
- Run `mypy` for type checking
- Run `bandit -r .` for security scanning
- Run `pytest --cov=<target>` if tests are present
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

> ⚠️ These steps are **not required** if the PR only changes documentation.

Code formatting (e.g., `black`, `isort`) is automatically handled by GitHub Actions — do **not** apply them manually.

---

## 📄 Documentation Translation

- Translated files must be placed under `docs/<lang>/`
- If translated using a language model (e.g., ChatGPT), include this disclaimer at the top:
  > _"This page was translated using ChatGPT, and some items may differ from the original content."_
- Do not overwrite existing translations without human review.

---

## ✅ Commit and PR Guidelines

- Commit messages must be short and in English.
- PR descriptions must clearly explain what was changed.
- If Python code was modified, include outputs of tests and code checks above.

---

## 🤖 AI-Generated PR Template (for agents)

If an AI agent opens a pull request, use the following **PR body**:

```md
### 🤖 AI-Generated Pull Request

This PR was automatically created by a language model agent (e.g., ChatGPT).

- Please verify the accuracy of translations or code.
- If documentation was translated, make sure the following disclaimer is included:
  > "This page was translated using ChatGPT, and some items may differ from the original content."
```

If the PR includes code changes, see [Code Quality and Validation](#code-quality-and-validation).

---

## 🌐 Language Policy for AI-Generated PRs

- All PR titles and descriptions should be written in **English by default**.
- If the PR affects only Korean-language documentation (e.g., `docs/ko/`), **Korean PR body is allowed**.
- If a user explicitly requests Korean, the PR body may be written in Korean.
