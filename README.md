# Disease-prediction
A probability calculator using Baye's Theorem to estimate survival chances of a disease based on past hospital data.

# 🧮 Disease prediction

A project that applies **Bayes' Theorem** to estimate the **percentage chance of survival** from a disease using historical hospital data. Designed to help understand real-world applications of Bayesian probability in medical diagnosis and survival prediction.

---

## 📌 Project Goal

Use Bayes' Theorem to:
- Calculate updated probabilities of survival based on prior knowledge and test results
- Demonstrate how probabilistic reasoning can be applied to healthcare analytics
- Provide an open-source tool for learning, research, or further development

---

## 📌 Render Link

https://disease-prediction-dbgi.onrender.com/

---

## What this project does

This project is a **Bayesian post-test probability calculator** for diagnostic tests.  
It demonstrates how Bayes’ theorem updates the probability of disease once you know a test result.

It is **not** a lifetime disease risk predictor or a survival model.  
Instead, it focuses on a fundamental clinical reasoning process:

> “How much more (or less) likely is this disease after seeing the test result?”

---

## How it works

Given:
- **Prior probability** – baseline chance of having the disease (e.g., prevalence or pre-test clinical suspicion)
- **Test sensitivity** – P(test positive | disease present)
- **Test specificity** – P(test negative | disease absent)
- **Observed test result** – either “positive” or “negative”

The calculator applies **Bayes’ theorem** to compute the **posterior probability**:
the updated probability that the patient has the disease *given the test result*.

---

## Why this matters

Diagnostic tests don’t provide certainty — they **shift probabilities**.  
This tool makes that reasoning explicit and transparent.

It can be useful as:
- An **educational resource** for medical students and data scientists learning Bayes’ theorem
- A **demo app** for understanding how diagnostic tests affect decision-making
- A foundation to expand toward multi-feature or longitudinal models later

---

## 💡 What is Bayes' Theorem?

Bayes' Theorem describes the probability of an event, based on prior knowledge of conditions related to the event. In medical terms, it helps in refining the **probability of survival or disease detection** after new data (like a test result) is observed.

> **Formula:**

```
P(A|B) = [P(B|A) * P(A)] / [P(B|A) * P(A) + P(B|¬A) * P(¬A)]
```

Where:
- **P(A)** = Prior probability (e.g., survival rate)
- **P(B|A)** = Probability of a positive test given survival
- **P(B|¬A)** = Probability of a positive test given no survival (false positive)
- **P(A|B)** = Updated probability (posterior) of survival after test

---

## 🛠️ Features

- 🧠 Implements Bayesian inference with custom inputs
- 📊 Accepts and processes CSV-based hospital data
- ⚙️ Simple, extensible Python script
- 👶 Beginner-friendly for open source contributors

---

## 🔍 Sample Use Case

> Given:
- Survival rate (prior): 90%
- Test correctly detects survival (sensitivity): 80%
- Test gives false survival prediction in death cases: 10%

### Output:
```
Updated probability of survival: 98.78%
```

---

## 🗂️ Project Structure

```
Disease-prediction/
├── run.py                        # Application entry point
├── hospital_data.csv             # Dataset used for probability calculations
├── backend/
│   ├── __init__.py               # Flask app factory
│   ├── routes/
│   │   └── disease_routes.py     # API endpoints and routing logic
│   ├── utils/
│   │   └── calculator.py         # Core Bayes' Theorem calculation logic
│   ├── static/
│   │   ├── script.js             # JavaScript for frontend interaction
│   │   └── style.css             # Styling for the frontend
│   └── templates/
│       ├── index.html            # Main HTML page served by Flask
│       └── updated_index.html    # Alternative HTML template
├── README.md                     # Project overview and usage
├── PROJECT_STRUCTURE.md          # Detailed guide explaining each file
├── CONTRIBUTING.md               # Contribution instructions
├── CODE_OF_CONDUCT.md            # Contributor behavior guidelines
├── LICENSE                       # License file
├── Scalability_report.txt        # Future expansion and scalability plans
└── .gitignore                    # Git ignored files

```
For a detailed, beginner-friendly explanation of what each file does, please read our guide:

➡️ **[View the Project Structure Guide](./PROJECT_STRUCTURE.md)**


---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/Disease-prediction.git
cd Disease-prediction
```

### (Optional) Create and activate a virtual environment
It's recommended to use a virtual environment to keep dependencies isolated.

- On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
- On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Requirements
```bash
pip install -r requirements.txt
```
### 3. Run the App
```bash
python run.py
```

### 4. Open in Browser
```bash
http://127.0.0.1:5000/
```

---

## ✅ Contributing

We love contributions—whether it's fixing a bug, improving docs, or adding a new feature. This quick guide will help you get started.

### 1) Fork and clone the repository
- Click the Fork button on GitHub to create your copy of the repo.
- Clone your fork locally:
```bash
# Replace YOUR-USERNAME with your GitHub username
git clone https://github.com/YOUR-USERNAME/Disease-prediction.git
cd Disease-prediction
```
- (Optional) Add the original repository as "upstream" to keep your fork updated:
```bash
git remote add upstream https://github.com/ORIGINAL-OWNER/Disease-prediction.git
# Verify remotes
git remote -v
```

### 2) Create a new branch
Create a branch for your change (do not work on main):
```bash
git checkout -b feat/short-description
# examples: feat/new-calculator-tests, fix/edge-case-handling, docs/improve-readme
```

### 3) Make changes and commit them
- Make your edits and run tests locally if applicable.
- Stage and commit with a clear message:
```bash
git add -A
git commit -m "feat: add XYZ with tests"  # use imperative, present tense
```
Tips:
- Keep commits focused and small.
- Write descriptive commit messages (use prefixes like feat, fix, docs, refactor, test, chore).

### 4) Push your branch and open a Pull Request (PR)
```bash
git push origin feat/short-description
```
- Go to your fork on GitHub and click "Compare & pull request".
- Provide a clear title and description:
  - What changed and why
  - Screenshots or logs if UI/behavior changed
  - Any limitations or follow-ups

### 5) Keep your branch up to date (optional but recommended)
If someone else merged changes into the main branch, update your branch:
```bash
# Fetch latest main from upstream and rebase your branch on top
git fetch upstream
git checkout main
git merge upstream/main
# or rebase if you prefer: git rebase upstream/main

git checkout feat/short-description
git rebase main
# Resolve conflicts if any, then continue: git add -A && git rebase --continue
```

### Basic contribution rules
- Follow Python style (PEP 8) and keep code simple and readable.
- Add or update tests when changing behavior.
- Update documentation for user-facing changes.
- One focused change per PR; smaller PRs are easier to review.
- Be respectful and follow our Code of Conduct.
- Before large features, open an issue to discuss the approach.

For more details, see our full guide: [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 🎓 Ideal For

- Students learning probability & statistics
- Open source contributors
- Anyone interested in real-world applications of Bayes’ Theorem

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Acknowledgements

This project was created and maintained by Alivia Hossain. Inspired by practical applications of statistics in healthcare.
