# 🚀 Quick Start: AI Recommendations

Get your Disease Prediction Calculator up and running with AI-powered recommendations in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `flask` - Web framework
- `google-generativeai` - Gemini API client
- `python-dotenv` - Environment variable management
- And other dependencies

## Step 2: Get Your Gemini API Key

1. **Go to**: [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. **Sign in** with your Google account
3. **Click** "Create API Key"
4. **Copy** the generated key

**Note**: The Gemini API has a free tier with generous limits!

## Step 3: Create .env File

In the project root directory (where `run.py` is located), create a file named `.env`:

```bash
# Windows PowerShell
New-Item .env -ItemType File

# Mac/Linux
touch .env
```

Add your API key to the file:

```
GEMINI_API_KEY=your_actual_api_key_here
```

**Important**: Replace `your_actual_api_key_here` with the key you copied in Step 2.

## Step 4: Run the Application

```bash
python run.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

## Step 5: Try It Out!

1. **Open browser**: Navigate to `http://127.0.0.1:5000/`

2. **Calculate a probability**:
   - Choose a disease from the dropdown OR
   - Enter custom probability values
   - Click "Calculate"

3. **Get AI recommendations**:
   - After seeing results, scroll down
   - Find the "AI-Powered Recommendations" card
   - Click "Get Recommendations"
   - Wait 2-3 seconds for AI response

4. **View recommendations**:
   - Read the interpretation
   - Review suggested next steps
   - Note the medical disclaimer

## ✅ Success Indicators

You'll know it's working when:
- ✓ No errors in the console when starting
- ✓ Application loads in browser
- ✓ Calculations work normally
- ✓ Recommendations section appears after calculation
- ✓ "Get Recommendations" button generates AI content

## ❌ Common Issues

### Issue: "API key not configured"

**Solution**:
- Verify `.env` file exists in project root
- Check API key has no extra spaces or quotes
- Restart the application

### Issue: "Module not found: google.generativeai"

**Solution**:
```bash
pip install google-generativeai
```

### Issue: Recommendations not showing

**Solution**:
- Check browser console for errors (F12)
- Verify you completed a calculation first
- Try refreshing the page

## 🎨 Bonus: Dark Mode

Toggle dark mode using the sun/moon icon in the top-right navbar!

## 📚 Need More Help?

- **Detailed Setup**: See [GEMINI_SETUP.md](GEMINI_SETUP.md)
- **Feature Overview**: See [AI_RECOMMENDATIONS_FEATURE.md](AI_RECOMMENDATIONS_FEATURE.md)
- **General Info**: See [README.md](README.md)

## 🔒 Security Reminder

- Never commit your `.env` file to Git
- Never share your API key publicly
- The `.gitignore` already excludes `.env` for safety

---

**That's it!** You now have AI-powered medical recommendations integrated into your Disease Prediction Calculator. 🎉

