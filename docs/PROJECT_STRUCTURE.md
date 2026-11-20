# 📂 Project Structure Explained: A Beginner's Guide

Hello! Welcome to the Disease Prediction project. If you're new to web development, all these files and folders might look confusing. Don't worry! This guide is here to explain the purpose of every file.

Think of this project like building a car:
-   The **Python/Flask** code is the **engine** (it does all the work).
-   The **HTML** is the **car's body and seats** (the structure you see and interact with).
-   The **CSS** is the **paint job and design** (making it look good).
-   The **JavaScript** is the **dashboard electronics** (like the radio and power windows).

Let's break it down file by file.

---

### The Core Logic

#### 📄 `run.py`
* **WHAT**: The application entry point. It creates the Flask app and starts the web server.
* **WHY**: It's the launchpad. Run `python run.py` and the site is live at http://127.0.0.1:5001.
* **HOW**: It calls `create_app()` from `backend/__init__.py`, which wires up the database, security settings and all the routes.

#### 📁 `backend/`
The whole Flask application lives here:

| Folder | What's inside |
|---|---|
| `routes/` | URL handlers ("blueprints"), e.g. the calculator, ML prediction, login, history |
| `models/` | Database tables (users, history) and the ML model |
| `utils/` | Helpers. `calculator.py` holds **all** Bayes' Theorem math |
| `services/` | Reusable business logic, e.g. saving prediction history |
| `middleware/` | Security (rate limiting), logging and error handling |
| `storage.py` | Decides where the app's database lives (`database/`) |

#### 📄 `backend/utils/calculator.py`
* **WHAT**: The pure mathematical logic for Bayes' Theorem.
* **WHY**: Separating the math from the web server code is called **"Separation of Concerns."** It lets us test the calculator without running the website.
* **HOW**: Functions take numbers (prior probability, sensitivity, …), validate them, and return the posterior probability. The routes call these functions whenever they need the math.

---

### 🖼️ The Frontend (What You See in the Browser)

#### 📁 `backend/templates/`
The folder where Flask looks for HTML files. They're called "templates" because they're fill-in-the-blank documents: placeholders like `{{ result }}` are replaced with real data before the page is sent to the browser. `base.html` is the shared layout that every other page extends.

#### 📁 `backend/static/`
"Static" files are sent to the browser unchanged: CSS (`style.css`), JavaScript (`script.js`) and images (`assets/`). HTML gives a page its structure, CSS its look, and JavaScript its interactivity.

---

### 💾 Data, Storage and Testing

#### 📄 `data/hospital_data.csv`
* **WHAT**: A CSV (Comma-Separated Values) file with each disease's prior probability, sensitivity and specificity.
* **WHY**: Keeping data separate from code means you can update the numbers without changing any code.
* **HOW**: The calculator routes read this file. `python scripts/preprocess.py` regenerates it from the raw datasets in `data/raw/`.

#### 📁 `database/`
Your local data: user accounts, password hashes and prediction history, in `disease_prediction.db`. It's created automatically and git-ignored.

#### 📁 `backend/tests/` and `tests/`
Automated tests. Run them all with `pytest backend/tests tests`.
* A **unit test** (e.g. `test_calculator.py`) checks one small piece, such as giving the calculator known inputs and comparing against the correct answer.
* An **integration test** (e.g. `test_integration.py`) checks that several pieces work together.

Tests use a temporary database, so they never touch your real data.

---

### 📜 Project Management & Community Files

These files don't run, but they are very important for explaining the project to other humans.

* **`README.md`**: The front page of the project. It tells visitors what the project does, why it's useful, and how to get it running.
* **`LICENSE`**: The legal document that explains how others are allowed to use your code. The MIT License is very popular because it's simple and allows people to do almost anything with the code.
* **`.gitignore`**: A list of files and folders that Git (our version control system) should ignore. This is used to prevent temporary files or secret information from being saved in the project's history.
* **`docs/CONTRIBUTING.md`**: A guide for other developers who want to contribute to the project. It explains the rules and the process for submitting changes.
* **`docs/CODE_OF_CONDUCT.md`**: Sets the rules for respectful and professional behavior within the project community, ensuring it's a welcoming space for everyone.