# 🧠 Disease Prediction System
An **ML-powered, educational web application** that demonstrates how **machine learning, Bayesian probability, and AI** can be used to estimate disease likelihood based on symptoms and diagnostic test results.

This project is designed to make **diagnostic reasoning transparent**, intuitive, and interactive - especially for students, researchers, and developers exploring medical ML concepts.

---
## ⚠️ Disclaimer

> **Educational Use Only**

This project is intended strictly for **learning, research, and demonstration purposes**.  
It is **not a medical tool** and must **not** be used for real-world diagnosis or treatment decisions.

Always consult a qualified healthcare professional for medical advice.

---
## ✨ Core Highlights
- 🔬 Combines **Machine Learning + Bayesian Inference**
- 📊 Visual comparison of **prior vs posterior probabilities**
- 🤖 AI-powered explanations & next-step recommendations
- 🌐 Multi-language support (English, Hindi, Gujarati, Tamil)
- 🌙 Dark mode for better accessibility
- 📘 Beginner-friendly educational explanations
---

## 📑 Table of Contents
- [Quick Start (30 seconds)](#-quick-start-30-seconds)
- [Key Features](#-key-features)
  - [Educational Features](#-educational-features)
  - [ML Features](#-ml-features)
  - [AI Features](#-ai-features)
  - [Project Structure](#project-structure)
  - [Getting Started](#getting-started-detailed)
- [Using AI-Powered Recommendations](#-using-ai-powered-recommendations)
- [Bayes’ Theorem Explained](#-bayes-theorem-explained)
- [Troubleshooting](#-troubleshooting)
- [Privacy & Data Handling](#-privacy--data-handling)
- [Dataset & Model](#-dataset--model)
- [License](#-license)
---

## 🚀 Quick Start (30 seconds)
```bash
git clone https://github.com/aliviahossain/Disease-prediction.git
cd Disease-prediction
pip install -r requirements.txt
python run.py
```
Open in your browser:
👉 http://127.0.0.1:5000/

That’s it 🎉

## 📌 Key Features
### 📘 Educational Features
- Clear explanations of Prior, Likelihood, and Posterior Probability
- Step-by-step visualization of Bayes’ Theorem
- Interactive probability sliders for experimentation
- Built-in glossary and help section
## 🤖 ML Features
- Symptom-based disease prediction
- Disease selection with predefined symptom sets
- ML-generated probability scores
- Risk categorization (Low / Medium / High)
## 🧠 AI Features
- AI-powered interpretation of probability results
- Suggested next steps (consultation, testing, lifestyle review)
- Multi-language AI output:
  - 🇬🇧 English
  - 🇮🇳 Hindi
  - 🇮🇳 Gujarati
  - 🇮🇳 Tamil

Powered by Google Gemini API

## 🗂️ Project Structure
```bash
Disease-prediction/
├── run.py                      # Application entry point
├── dashboard.py                # Streamlit interactive dashboard
├── requirements.txt            # Python dependencies
├── hospital_data.csv           # Sample statistical data
├── backend/
│   ├── routes/                 # Flask routes (auth, ML, calculator)
│   ├── models/                 # Database & ML models
│   ├── utils/                  # Bayesian calculator & AI helpers
│   ├── static/                 # JS & CSS
│   └── templates/              # HTML templates
├── README.md
├── LICENSE
└── Scalability_report.txt
```
## 🛠️ Getting Started (Detailed)
## 1️⃣ Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```
## 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```
## 3️⃣ Run the Application
```bash
python run.py
```
## 🤖 Using AI-Powered Recommendations
Enable Gemini AI (Optional but Recommended)

**Step 1: Get an API Key**

Get your free API key from Google AI Studio

**Step 2: Configure the API Key**

Using `.env` file (recommended):
```env
GEMINI_API_KEY=your_api_key_here
```
**Or via environment variable:**
```bash
export GEMINI_API_KEY=your_api_key_here   # macOS/Linux
```
## How It Works
1) Calculate disease probability
2) Choose a language 🌐
3) Click “**Get AI Recommendations**”
4) Receive:
    - Probability interpretation
    - Suggested next actions
    - Medical disclaimers
## 🧮 Bayes’ Theorem Explained
Bayes’ Theorem updates the probability of a condition after observing new evidence, such as a test result.
### **Formula:**
```java
P(A|B) = [P(B|A) × P(A)] / [P(B|A) × P(A) + P(B|¬A) × P(¬A)]
```
Where:
- **P(A)** → Prior probability
- **P(B|A)** → Sensitivity
- **P(B|¬A)** → False positive rate
- **P(A|B)** → Posterior probability

This project visualizes this shift clearly using charts and explanations.
## 🔧 Troubleshooting
### AI Not Working?
- Ensure `GEMINI_API_KEY` is set
- Restart the application
- Check internet connectivity
- Verify API quota availability
### App Not Starting?
- Confirm Python ≥ 3.9
- Reinstall dependencies
- Activate virtual environment
## 🔒 Privacy & Data Handling

All image processing and probability calculations are performed **locally** on the user’s machine.  
No images, symptoms, or personal data are uploaded, stored, or shared externally by default.


## 🧠 Model Architecture

The eye-disease image classification model is based on a deep convolutional neural network using a ResNet architecture inspired by:

He, K., Zhang, X., Ren, S., & Sun, J. (2016).  
*Deep Residual Learning for Image Recognition*. Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR).


## 📊 Dataset Sources

The eye-disease image prediction model was trained using the following publicly available dataset from Kaggle:

- **Eye Diseases Classification Dataset**  
  https://www.kaggle.com/datasets/gunavenkatdoddi/eye-diseases-classification

This dataset includes labeled images for:

- Normal eyes
- Glaucoma
- Diabetic Retinopathy
- Cataract

The skin-disease image prediction model was trained using the following publicly available dataset from Kaggle:

- **Skin Diseases Image Dataset**
  https://www.kaggle.com/datasets/ismailpromus/skin-diseases-image-dataset

This dataset includes labeled images for the following conditions:

- Atopic Dermatitis
- Basal Cell Carcinoma
- Benign Keratosis-like Lesions
- Eczema
- Melanocytic Nevi
- Melanoma
- Psoriasis
- Seborrheic Keratoses and other Benign Tumors
- Tinea Ringworm, Candidiasis, and other Fungal Infections
- Warts, Molluscum, and other Viral Infections

All dataset credits belong to their respective authors and contributors. 
This project does not claim ownership of the dataset. Please refer to the dataset page for licensing and usage terms.

- All computations run locally
- No personal data is stored or transmitted
- AI requests only include probability values (no user identity)
## 📊 Dataset & Model
###  Dataset
- Eye Diseases Classification Dataset (Kaggle)
   - Normal
   - Glaucoma
   - Diabetic Retinopathy
   - Cataract
### Model Architecture
- CNN based on ResNet
- Inspired by He et al., 2016 - Deep Residual Learning

## 📜 License
This project is licensed under the MIT License. See the [LICENSE](https://github.com/aliviahossain/Disease-prediction/blob/main/LICENSE) file for details.
## 🙌 Acknowledgements
Created and maintained by Alivia Hossain.

Contributions are welcome, feel free to open issues or pull requests.

**⭐ If you find this project useful, consider giving it a star!**