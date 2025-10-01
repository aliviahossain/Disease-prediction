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

## ⚠️ Disclaimer

This project is intended **for educational and demonstration purposes only**.  
It is **not a medical device** and must **not be used for clinical decision-making** or patient care.

Probabilities and outputs are based on simplified statistical assumptions and example data.  
Real clinical practice requires professional judgment, validated tools, and regulatory approval.

If you are a patient, please consult a qualified healthcare provider.  
If you are a developer or student, treat this project as a learning resource for Bayes’ theorem, not as a diagnostic instrument.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Acknowledgements

This project was created and maintained by Alivia Hossain. Inspired by practical applications of statistics in healthcare.
