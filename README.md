# Probability-Calculator
A probability calculator using Baye's Theorem to estimate survival chances of a disease based on past hospital data.

# 🧮 Probability Calculator

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
│
├── data/                 # Sample hospital datasets
├── src/                  # Source code and logic
│   └── calculator.py     # Main Bayes calculator script
├── tests/                # Unit and validation tests
├── README.md             # Project documentation
├── CONTRIBUTING.md       # Guidelines for contributors
├── requirements.txt      # Python dependencies
└── LICENSE               # Open source license (MIT)
```

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/Probability-Calculator.git
cd Probability-Calculator
```

### 2. Install Requirements
```bash
pip install -r requirements.txt
```

### 3. Run the Calculator
```bash
python src/calculator.py
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
