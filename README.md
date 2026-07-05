# 🧠 Disease Prediction System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Backend-black?style=for-the-badge&logo=flask)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)
![Educational](https://img.shields.io/badge/Purpose-Educational-orange?style=for-the-badge)

**An ML-powered web app that uses Bayes' Theorem and machine learning to estimate disease likelihood from symptoms — built for students, researchers, and developers.**

[🚀 Live Demo](https://disease-prediction-nwnu.onrender.com) · [🐛 Report a Bug](https://github.com/aliviahossain/Disease-prediction/issues) · [💡 Request a Feature](https://github.com/aliviahossain/Disease-prediction/issues)

</div>

---

> ⚠️ **Disclaimer: Educational Use Only**
> This project is for learning and demonstration purposes only. It is **not** a medical tool and must **not** be used for real-world diagnosis or treatment. Always consult a qualified healthcare professional.

---

## 📋 Table of Contents

- [About the Project](#-about-the-project)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Detailed Setup](#️-detailed-setup)
- [How It Works](#-how-it-works)
- [Project Structure](#-project-structure)
- [Dataset & Model](#-dataset--model)
- [Privacy & Data Handling](#-privacy--data-handling)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔍 About the Project

The Disease Prediction System makes **medical reasoning transparent and interactive**. It combines classical Bayesian probability with modern ML to show users not just *what* a prediction is, but *why* — step by step.

It's designed to bridge the gap between complex statistical concepts and intuitive understanding, with visual charts, AI-powered explanations, and multi-language support.

---

## ✨ Key Features

### 📘 Educational
| Feature | Description |
|---|---|
| Bayes' Theorem Visualizer | Step-by-step breakdown of prior → posterior probability |
| Interactive Sliders | Experiment with probability values in real time |
| Built-in Glossary | Plain-English definitions of medical/statistical terms |

### 🤖 ML & Prediction
| Feature | Description |
|---|---|
| Symptom-Based Prediction | Select symptoms to get ML-generated probability scores |
| BMI Integration | Height/weight inputs contribute to risk estimation |
| Risk Categorization | Results classified as Low / Medium / High risk |
| Prediction History | Stored timeline of past predictions with analytics |

### 🧠 AI Features
| Feature | Description |
|---|---|
| AI Explanations | Gemini-powered interpretation of results |
| Next-Step Guidance | Suggests consultation, testing, or lifestyle review |
| Multi-Language Output | English 🇬🇧 · Hindi 🇮🇳 · Gujarati 🇮🇳 · Tamil 🇮🇳 |

### 📊 Analytics Dashboard
- Comparative probability trend charts
- Risk distribution graphs
- Historical prediction tables

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| ML / Math | Bayesian Inference, ResNet CNN |
| AI | Google Gemini API |
| Dashboard | Streamlit |
| Data | CSV (hospital_data.csv) |

---

## 🚀 Quick Start

**Option 1 — View Online (instant, no setup)**
👉 [https://disease-prediction-nwnu.onrender.com](https://disease-prediction-nwnu.onrender.com)

**Option 2 — Run Locally (30 seconds)**

```bash
git clone https://github.com/aliviahossain/Disease-prediction.git
cd Disease-prediction
pip install -r requirements.txt
python run.py
```

Then open your browser at: **http://127.0.0.1:5001/**

---

## 🛠️ Detailed Setup

### 1. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate         # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. (Optional) Enable AI Recommendations

Get a free API key from [Google AI Studio](https://aistudio.google.com/), then set it:

```bash
# Option A: .env file (recommended)
echo "GEMINI_API_KEY=your_key_here" > .env

# Option B: Environment variable
export GEMINI_API_KEY=your_key_here    # macOS / Linux
set GEMINI_API_KEY=your_key_here       # Windows
```

### 4. Run the App

```bash
python run.py
```

---
## 📦 Deployment

The application can be deployed to Google Cloud Run.

See:
docs/deployment/gcp-cloud-run.md

See [docs/deployment/gcp-cloud-run.md](docs/deployment/gcp-cloud-run.md) for deployment instructions.

---
## 🧮 How It Works

### Bayes' Theorem

The app updates disease probability after observing symptoms or test results using:

```
P(Disease | Evidence) = [ P(Evidence | Disease) × P(Disease) ]
                        ─────────────────────────────────────────────────────────
                        [ P(Evidence | Disease) × P(Disease) + P(Evidence | No Disease) × P(No Disease) ]
```

| Term | Meaning |
|---|---|
| `P(Disease)` | Prior probability — baseline disease prevalence |
| `P(Evidence\|Disease)` | Sensitivity — how often evidence appears given disease |
| `P(Evidence\|No Disease)` | False positive rate |
| `P(Disease\|Evidence)` | Posterior — updated probability after new evidence |

### BMI Integration

The system accepts height (cm) and weight (kg) to compute BMI, which adjusts risk estimates:

```
BMI = weight (kg) / (height in meters)²
```

| BMI Range | Category |
|---|---|
| Below 18.5 | Underweight |
| 18.5 – 24.9 | Normal |
| 25 – 29.9 | Overweight |
| 30+ | Obese |

---

## 🗂️ Project Structure

```
Disease-prediction/
├── run.py                         # App entry point
├── dashboard.py                   # Streamlit analytics dashboard
├── requirements.txt               # Python dependencies
├── hospital_data.csv              # Bayesian stats (generated by pipeline)
├── data/
│   ├── raw/                       # Original datasets (git-ignored)
│   ├── cleaned/
│   │   └── hospital_data_cleaned.csv
│   └── preprocess.py              # Data pipeline script
├── backend/
│   ├── routes/                    # Flask routes (auth, ML, calculator)
│   ├── models/                    # Database & ML models
│   ├── utils/                     # Bayesian calculator & AI helpers
│   ├── static/                    # JS & CSS
│   └── templates/                 # HTML templates
├── README.md
└── LICENSE
```

---

## 📊 Dataset & Model

### Bayesian Calculator Datasets

| Disease | Dataset | Source |
|---|---|---|
| Heart Disease | UCI Heart Disease Dataset | [UCI Repository](https://archive.ics.uci.edu/dataset/45/heart+disease) |
| Diabetes | Pima Indians Diabetes Dataset | [Kaggle](https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database) |
| Breast Cancer | Breast Cancer Wisconsin | [UCI Repository](https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic) |

To regenerate `hospital_data.csv` from raw datasets:
```bash
python data/preprocess.py
```
> Raw dataset files are not committed to this repo. Download them from the links above and place them in `data/raw/`.

### Image Classification Datasets

| Model | Dataset | Conditions |
|---|---|---|
| Eye Disease CNN | [Eye Diseases Classification (Kaggle)](https://www.kaggle.com/datasets/gunavenkatdoddi/eye-diseases-classification) | Glaucoma, Diabetic Retinopathy, Cataract, Normal |
| Skin Disease CNN | [Skin Diseases Image Dataset (Kaggle)](https://www.kaggle.com/datasets/ismailpromus/skin-diseases-image-dataset) | Melanoma, Eczema, Psoriasis, and 7 others |

The CNN architecture is based on ResNet, inspired by He et al. (2016) — *Deep Residual Learning for Image Recognition*.

---

## 🔒 Privacy & Data Handling

- ✅ All calculations run **locally** on your machine
- ✅ No symptoms, images, or personal data are uploaded or stored externally
- ✅ AI requests only transmit probability values — never user identity
- ✅ Prediction history is stored locally using JSON-based storage

---

## 🔧 Troubleshooting

<details>
<summary><b>AI recommendations not working?</b></summary>

- Make sure `GEMINI_API_KEY` is set correctly
- Restart the application after setting the key
- Check your internet connection
- Verify your API quota at [Google AI Studio](https://aistudio.google.com/)
</details>

<details>
<summary><b>App not starting?</b></summary>

- Confirm Python version is **3.9 or higher**: `python --version`
- Activate your virtual environment before running
- Reinstall dependencies: `pip install -r requirements.txt`
</details>

---

## 🤝 Contributing

Contributions are warmly welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a new branch: `git checkout -b feature/your-feature-name`
3. **Make** your changes and commit: `git commit -m "Add: your meaningful message"`
4. **Push** to your fork: `git push origin feature/your-feature-name`
5. **Open** a Pull Request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Created and maintained by [Alivia Hossain](https://github.com/aliviahossain)

⭐ If you find this project useful, consider giving it a star!

</div>