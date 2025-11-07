# Gemini API Setup Guide

This application now includes AI-powered recommendations using Google's Gemini API. After calculating disease probabilities, you can get personalized next-step recommendations.

## 🔑 Getting Your Gemini API Key

1. **Visit Google AI Studio**
   - Go to [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
   - Sign in with your Google account

2. **Create a New API Key**
   - Click on "Create API Key"
   - Select or create a project
   - Copy the generated API key

3. **Keep Your API Key Secure**
   - Never commit your API key to version control
   - Don't share it publicly
   - Treat it like a password

## ⚙️ Configuration

### Method 1: Using .env File (Recommended for Development)

1. Create a `.env` file in the project root directory:
   ```bash
   touch .env
   ```

2. Add your API key to the `.env` file:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

3. The application will automatically load this when you run it

### Method 2: Using Environment Variables (Production)

Set the environment variable directly in your terminal or hosting platform:

**Linux/Mac:**
```bash
export GEMINI_API_KEY=your_actual_api_key_here
```

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_actual_api_key_here"
```

**Heroku/Render/Other Cloud Platforms:**
- Add `GEMINI_API_KEY` as an environment variable in your platform's settings

## 🚀 Installation

1. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up your API key** (see Configuration section above)

3. **Run the application:**
   ```bash
   python run.py
   ```

## 📱 How to Use

1. **Calculate Disease Probability**
   - Use either the preset hospital data or enter custom values
   - Click "Calculate"

2. **Get AI Recommendations**
   - After seeing your results, an "AI-Powered Recommendations" section will appear
   - Click the "Get Recommendations" button
   - Wait a few seconds for Gemini to generate personalized advice

3. **Review Recommendations**
   - The AI will provide:
     - Interpretation of your probability results
     - Recommended next steps
     - Important considerations

## 🔒 Privacy & Security

- **Your data stays secure**: API calls are made server-side, not from the browser
- **No data storage**: We don't store your API key or calculation data
- **Educational purposes**: Recommendations are for educational purposes only, not medical advice

## ❗ Troubleshooting

### "API key not configured" Error
- Make sure your `.env` file exists in the project root
- Verify the API key is correct (no extra spaces or quotes)
- Restart the application after adding the API key

### "Unable to generate recommendations" Error
- Check your internet connection
- Verify your API key is valid and active
- Check if you've exceeded your API quota (Gemini has free tier limits)

### API Key Not Loading
- Ensure `python-dotenv` is installed: `pip install python-dotenv`
- Check that `.env` is in the same directory as `run.py`
- Try setting the environment variable manually (Method 2)

## 💡 API Limits

Gemini API has usage limits:
- **Free tier**: 60 requests per minute
- **Rate limiting**: May occur during high usage
- **Monitor usage**: Check your [Google Cloud Console](https://console.cloud.google.com/)

## 📚 Additional Resources

- [Gemini API Documentation](https://ai.google.dev/docs)
- [Google AI Studio](https://makersuite.google.com/)
- [API Pricing](https://ai.google.dev/pricing)

## ⚠️ Important Disclaimer

The AI-generated recommendations are for **educational purposes only** and should not be used as a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of qualified healthcare providers with any questions regarding medical conditions.

