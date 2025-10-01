## What this project does

This project is a **Bayesian post-test probability calculator** for diagnostic tests.  
It demonstrates how Bayes’ theorem updates the probability of disease once you know a test result.

It is **not** a lifetime disease risk predictor or a survival model.  
Instead, it focuses on a fundamental clinical reasoning process:

> “How much more (or less) likely is this disease after seeing the test result?”


## How it works

Given:
- **Prior probability** – baseline chance of having the disease (e.g., prevalence or pre-test clinical suspicion)
- **Test sensitivity** – P(test positive | disease present)
- **Test specificity** – P(test negative | disease absent)
- **Observed test result** – either “positive” or “negative”

The calculator applies **Bayes’ theorem** to compute the **posterior probability**:
the updated probability that the patient has the disease *given the test result*.


## Clinical example

Suppose:
- Disease prevalence = 10% (prior probability = 0.10)
- Test sensitivity = 90%
- Test specificity = 95%

**Case 1: Positive test result**  
\[
P(\text{disease | positive}) = \frac{0.9 \times 0.10}{(0.9 \times 0.10) + (0.05 \times 0.90)} \approx 67\%
\]

**Case 2: Negative test result**  
\[
P(\text{disease | negative}) = \frac{0.10 \times (1 - 0.90)}{(0.10 \times 0.10) + (0.95 \times 0.90)} \approx 1.1\%
\]

So the test increases disease probability from **10% to ~67%** when positive,  
and decreases it to **~1%** when negative.

## Why this matters

Diagnostic tests don’t provide certainty — they **shift probabilities**.  
This tool makes that reasoning explicit and transparent.

It can be useful as:
- An **educational resource** for medical students and data scientists learning Bayes’ theorem
- A **demo app** for understanding how diagnostic tests affect decision-making
- A foundation to expand toward multi-feature or longitudinal models later


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
Probability-Calculator/
├── app.py                       # Main Flask application
├── hospital_data.csv           # Dataset used for probability calculations
├── src/
│   └── calculator.py           # Core logic using Bayes' Theorem
├── static/
│   ├── script.js               # JavaScript for frontend interaction
│   └── style.css               # Styling for the frontend
├── templates/
│   └── index.html              # HTML page served by Flask
├── tests/
│   └── test_calculator.py      # Unit tests for the calculator logic
├── README.md                   # Project overview and usage
├── LICENSE                     # License file
├── .gitignore                  # Git ignored files
├── CODE_OF_CONDUCT.md         # Contributor behavior guidelines
├── CONTRIBUTING.md            # Contribution instructions

```

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/Disease-prediction.git
cd Probability-Calculator
```

### 2. Install Requirements
```bash
pip install Flask
```

### 3. Run the App
```bash
python app.py
```

### 4. Open in Browser
```bash
http://127.0.0.1:5000/
```

---

## ✅ Contributing

New to open source? We welcome all contributors! Here's how to get started:
- 🌱 Check out `Issues`
- 🛠 Add features or improve existing ones
- 📝 Help with documentation
- 🧪 Add new test cases

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file before making a pull request.

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
