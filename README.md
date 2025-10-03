# Disease-prediction
A probability calculator using Bayes' Theorem to estimate survival chances of a disease based on past hospital data.

# 🧮 Disease Prediction

A project that applies **Bayes' Theorem** to estimate the **percentage chance of survival** from a disease using historical hospital data.  
Designed to help understand real-world applications of Bayesian probability in medical diagnosis and survival prediction.

---

## 📌 Project Goal

Use Bayes' Theorem to:
- Calculate updated probabilities of survival based on prior knowledge and test results
- Demonstrate how probabilistic reasoning can be applied to healthcare analytics
- Provide an open-source tool for learning, research, or further development

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
- ⚙️ Flask-based web application
- 🧪 Includes unit & integration tests
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

Disease-prediction/
├── backend/ # Core application logic
│ └── calculator.py # Bayes’ theorem implementation
├── hospital_data.csv # Dataset used for probability calculations
├── run.py # Main Flask application
├── tests/ # Unit and integration tests
├── static/ # JS & CSS for frontend (if any)
├── templates/ # HTML templates for Flask
├── README.md # Project overview and usage
├── requirements.txt # Python dependencies
├── LICENSE # License file
├── CODE_OF_CONDUCT.md # Contributor guidelines
├── CONTRIBUTING.md # Contribution instructions
├── PROJECT_STRUCTURE.md # Detailed project structure explanation

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/Disease-prediction.git
cd Disease-prediction

2. Install Requirements
pip install -r requirements.txt

3. Run the App
python run.py

4. Open in Browser
http://127.0.0.1:5000/



✅ Contributing

New to open source? We welcome all contributors! Here's how to get started:

🌱 Check out Issues

🛠 Add features or improve existing ones

📝 Help with documentation

🧪 Add new test cases

Read the CONTRIBUTING.md
 file before making a pull request.

🎓 Ideal For

Students learning probability & statistics

Open source contributors

Anyone interested in real-world applications of Bayes’ Theorem

📜 License

This project is licensed under the MIT License
.

🙌 Acknowledgements

This project was created and maintained by Alivia Hossain.
Inspired by practical applications of statistics in healthcare.