# Disease-prediction
The ML-Powered Disease Prediction System is a comprehensive web application designed to demonstrate the likelihood of specific diseases based on user-selected symptoms and statistical data. It serves as both an educational resource for understanding diagnostic probabilities and a demonstration of how machine learning and Bayesian probability can be applied in clinical contexts.

The system features two core functionalities:

1.Symptom-Based Prediction (ML & Bayesian): Predicts disease probability based on selected symptoms.
 
2.Bayesian Probability Calculator: Allows users to calculate posterior disease probability using Bayes' Theorem based on prior probability, test characteristics (Sensitivity/Specificity), and test results.

---

## 📌 Key Features

1.Symptom-Based Prediction (Home)

Disease Selection: Users can select a specific disease (e.g., Influenza, Diabetes Type 2) from a dropdown list.

Symptom Input: A comprehensive list of associated symptoms allows users to select which ones they are experiencing.

Dual Prediction Results: Displays the likelihood of the disease using two distinct methods:

ML Prediction: A raw probability calculated by the underlying Machine Learning model.

Bayesian Analysis: Detailed probabilistic breakdown including Prior Probability, Likelihood, and Posterior Probability.

Risk Assessment: Provides a quick, clear risk label (e.g., "Low Risk").

2.Bayesian Probability Calculator (Calculator)

This module is designed for educational and analytical purposes, allowing users to explore the impact of diagnostic testing.

Pre-loaded Data: Select a disease to automatically load sample Prior Probability, Sensitivity, and Specificity data.

Custom Data Entry: Users can manually input:

Prior Probability P(D)

Test Sensitivity P(Pos|D)

False Positive Rate P(Pos|No D)

Test Result (Positive or Negative)

Probability Comparison: A clear bar chart visually compares the Prior Probability (initial belief) with the Posterior Probability (updated belief after the test result).

AI-Powered Recommendations: Provides an interpretation of the results and suggests Recommended Next Steps (e.g., Confirmative Testing, Medical Consultation, Lifestyle Review) in multiple languages (English and Hindi demonstrated).

3.Scalability

A detailed report on future scalability of project.

4.Glossary & Help Section (Help)

Key Terminology: Clear definitions for essential concepts in diagnostic probability: Prior Probability, Sensitivity, Specificity, False Positive Rate, and Posterior Probability.

Bayes' Theorem Explanation: A detailed, accessible explanation of the probabilistic theory underpinning the calculator.

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
- 🤖 AI-powered recommendations using Google Gemini API
- 🌐 Multi-language support (English, Hindi, Gujarati, Tamil)
- 🌙 Dark mode toggle for better viewing experience
- ⚙️ Simple, extensible Python script

---

## 🗂️ Project Structure

```
Disease-prediction/
├── run.py                        # Application entry point
├── hospital_data.csv             # Dataset used for probability calculations
├── .env                          # Environment variables (API keys) - create this file
├── backend/
│   ├── __init__.py               # Flask app factory
│   ├── routes/
│   │   └── disease_routes.py     # API endpoints and routing logic
│   │   └── general_routes.py     # routing logic
│   │   └── ml_routes.py          # Machine Learning and routing logic
│   │   └── scalability_routes.py     # routing logic
│   ├── utils/
│   │   ├── calculator.py         # Core Bayes' Theorem calculation logic
│   │   └── gemini_helper.py      # Gemini AI integration for recommendations
│   ├── static/
│   │   ├── script.js             # JavaScript for frontend interaction
│   │   └── style.css             # Styling for the frontend
│   └── templates/
│       ├── base.html             # Base HTML template
│       ├── calculator.html       # Probability calculator page
│       └── help.html             # Help and documentation page
│       └── home.html             # Main ML application page
│       └── Scalability.html      # Scalability page
├── README.md                     # Project overview and usage
├── LICENSE                       # License file
├── requirements.txt              # Python dependencies
├── Scalability_report.txt        # Future expansion and scalability plans
└── .gitignore                    # Git ignored files

```

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/Disease-prediction.git
cd DISEASE-PREDICTION-MAIN
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

### 3. Set Up Gemini API (Optional but Recommended)
To enable AI-powered recommendations:

#### Step 1: Get Your API Key
Get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

#### Step 2: Configure the API Key

**Option A: Using .env file (Recommended)**
Create a `.env` file in the project root directory:
```bash
GEMINI_API_KEY=your_api_key_here
```

**Option B: Set Environment Variable**
- **Windows (PowerShell):**
  ```powershell
  $env:GEMINI_API_KEY="your_api_key_here"
  ```
- **Linux/Mac:**
  ```bash
  export GEMINI_API_KEY=your_api_key_here
  ```

#### Step 3: Verify API Key Setup
After setting up your API key, you can verify it's working by checking the application logs when you start the server. The app will automatically detect and use available Gemini models.

**Note:** The app works without the API key, but AI recommendations won't be available.

### 4. Run the App
```bash
python run.py
```

### 5. Open in Browser
```bash
http://127.0.0.1:5000/
```

---

## 🤖 Using AI-Powered Recommendations

Once your Gemini API key is configured, you can get personalized medical recommendations:

1. **Calculate Disease Probability**
   - Select a disease from the dropdown or enter custom values
   - Click "Calculate" to see the probability results

2. **Choose Your Language** 🌐
   - Select your preferred language from the dropdown:
     - 🇬🇧 **English**
     - 🇮🇳 **हिंदी (Hindi)**
     - 🇮🇳 **ગુજરાતી (Gujarati)**
     - 🇮🇳 **தமிழ் (Tamil)**

3. **Get AI Recommendations**
   - After calculation, look for the "AI-Powered Recommendations" section
   - Choose your preferred language from the dropdown
   - Click the "Get Recommendations" button
   - Wait a few seconds for the AI to generate personalized advice

4. **Review the Output**
   The AI will provide:
   - 📊 **Interpretation** of your probability results in plain language
   - 🎯 **Recommended Next Steps** (e.g., further testing, specialist consultation)
   - ⚠️ **Important Considerations** and medical disclaimers

**Example Output (English):**
```
Interpretation:
Before the test, the probability was 15%. After a positive test result, 
the probability has increased to 85%, indicating a high likelihood.

Recommended Next Steps:
1. Consult a physician immediately for confirmatory tests
2. Discuss specialist referral (e.g., endocrinologist for diabetes)
3. Begin discussing lifestyle modifications with your doctor
...
```

**Example Output (Hindi/हिंदी):**
```
व्याख्या:
परीक्षण से पहले, संभावना 15% थी। सकारात्मक परीक्षण परिणाम के बाद, 
संभावना बढ़कर 85% हो गई है, जो उच्च संभावना को दर्शाती है।

अनुशंसित अगले कदम:
1. पुष्टिकरण परीक्षणों के लिए तुरंत चिकित्सक से परामर्श लें
2. विशेषज्ञ रेफरल पर चर्चा करें (जैसे मधुमेह के लिए एंडोक्राइनोलॉजिस्ट)
3. अपने डॉक्टर के साथ जीवनशैली में बदलाव पर चर्चा शुरू करें
...
```

---

## 🔧 Troubleshooting

### API Key Issues

**Problem: "API key not configured" error**
- ✅ Ensure your `.env` file exists in the project root
- ✅ Verify the API key has no extra spaces or quotes
- ✅ Restart the application after adding the API key
- ✅ Check that `python-dotenv` is installed: `pip install python-dotenv`

**Problem: "Unable to generate recommendations" error**
- ✅ Check your internet connection
- ✅ Verify your API key is valid at [Google AI Studio](https://makersuite.google.com/app/apikey)
- ✅ Check if you've exceeded your API quota (free tier: 60 requests/minute)
- ✅ Try restarting the application

**Problem: Environment variable not loading**
- On Windows PowerShell, try setting it directly:
  ```powershell
  $env:GEMINI_API_KEY="your_api_key_here"
  python run.py
  ```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Acknowledgements

This project was created and maintained by Alivia Hossain.
