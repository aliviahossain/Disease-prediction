# 🤖 AI-Powered Recommendations Feature

## Overview

After calculating disease probabilities using Bayes' Theorem, users can now get AI-powered recommendations for what to do next. This feature uses Google's Gemini API to provide contextual, educational guidance based on the calculation results.

## How It Works

### 1. User Flow

```
Calculate Probability → View Results → Click "Get Recommendations" → Receive AI Guidance
```

### 2. What Happens Behind the Scenes

1. **User calculates probability**
   - Either using preset hospital data OR custom inputs
   - Results are displayed with a probability comparison chart

2. **AI Recommendations section appears**
   - A new card appears with a "Get Recommendations" button
   - User can choose to get AI insights

3. **Gemini API generates recommendations**
   - The system sends:
     - Disease name (if using preset data)
     - Prior probability (before test)
     - Posterior probability (after test)
     - Test result (positive/negative)
   
4. **Personalized recommendations displayed**
   - Interpretation of the probabilities
   - Recommended next steps
   - Important considerations
   - Medical disclaimer

## What the AI Provides

### Interpretation
Clear, plain-language explanation of what the probability numbers mean.

**Example:**
> "A posterior probability of 78% indicates a relatively high likelihood of the disease given a positive test result, compared to the prior probability of 15%."

### Recommended Next Steps
2-4 actionable recommendations such as:
- Further diagnostic tests
- Consultation with specialists
- Monitoring and follow-up
- Lifestyle modifications
- Additional screening

### Important Considerations
- Context about test accuracy
- Factors that might influence results
- When to seek immediate medical attention
- Limitations of probabilistic diagnosis

## Technical Implementation

### Files Modified/Created

1. **backend/utils/gemini_helper.py** (NEW)
   - Gemini API integration
   - Prompt engineering for medical context
   - Error handling

2. **backend/routes/disease_routes.py** (MODIFIED)
   - New `/gemini-recommendations` endpoint
   - Handles API requests from frontend

3. **backend/static/script.js** (MODIFIED)
   - `getAIRecommendations()` function
   - Loading states and error handling
   - Markdown-to-HTML formatting

4. **backend/templates/main.html** (MODIFIED)
   - New recommendations container
   - Loading spinner
   - Disclaimer section

5. **backend/static/style.css** (MODIFIED)
   - Styling for recommendations section
   - Dark mode support
   - Responsive design

6. **requirements.txt** (MODIFIED)
   - Added `google-generativeai`
   - Added `python-dotenv`

7. **run.py** (MODIFIED)
   - Loads environment variables from .env

### API Endpoint

```python
POST /gemini-recommendations

Request Body:
{
  "disease_name": "Diabetes",  // Optional, can be null
  "prior_probability": 0.15,
  "posterior_probability": 0.78,
  "test_result": "positive"
}

Response:
{
  "success": true,
  "recommendations": "**Interpretation:**\n\n...",
  "prior_probability": 0.15,
  "posterior_probability": 0.78
}
```

## User Experience Features

### Loading States
- Smooth button transition to loading spinner
- "Generating AI recommendations..." message
- Professional animation

### Error Handling
- Graceful degradation if API key not configured
- Clear error messages
- Retry button on failure

### Visual Design
- Card-based layout consistent with the app
- Green accent color for AI branding
- Markdown-style formatting for readability
- Medical disclaimer always visible

### Dark Mode Support
- All recommendation styles support dark mode
- Proper contrast ratios maintained
- Smooth transitions between modes

## Security & Privacy

### API Key Protection
- Stored in `.env` file (not committed to Git)
- Loaded server-side only
- Never exposed to client

### Data Privacy
- No user data is stored
- API calls are made server-side
- No tracking or analytics on recommendations

### Rate Limiting
- Gemini API: 60 requests/minute (free tier)
- Handled gracefully with error messages

## Educational Value

### For Students
- Demonstrates practical AI integration
- Shows prompt engineering techniques
- Teaches API error handling
- Example of progressive enhancement

### For Medical Students
- Contextualizes probabilistic diagnosis
- Provides next-step reasoning
- Reinforces Bayesian thinking
- Educational disclaimers emphasize limitations

## Future Enhancements

### Possible Improvements
1. **Multi-language support** - Recommendations in different languages
2. **Conversation history** - Save and compare recommendations
3. **Custom prompts** - Let users ask specific questions
4. **Citation system** - Link to medical resources
5. **PDF export** - Download recommendations as PDF
6. **Severity levels** - Color-code urgency of recommendations

### Advanced Features
- Integration with medical databases
- Comparison with similar cases
- Risk factor analysis
- Timeline projections
- Treatment options database

## Testing

### Manual Testing Checklist
- [ ] Preset disease calculation triggers recommendations
- [ ] Custom input calculation triggers recommendations
- [ ] Button click shows loading state
- [ ] Successful API call displays recommendations
- [ ] Error handling works without API key
- [ ] Dark mode styles apply correctly
- [ ] Mobile responsive design works
- [ ] Disclaimer is always visible

### Test Cases
```javascript
// Test 1: Successful recommendation generation
// Test 2: API key missing error
// Test 3: Network failure handling
// Test 4: Markdown formatting display
// Test 5: Multiple calculations in sequence
```

## Troubleshooting

See [GEMINI_SETUP.md](GEMINI_SETUP.md) for detailed troubleshooting steps.

## Credits

- **Gemini API**: Google's generative AI platform
- **Integration**: Built for Disease Prediction Calculator
- **Purpose**: Educational enhancement for medical informatics

---

**Remember**: These are AI-generated recommendations for educational purposes only. Always consult healthcare professionals for medical advice.

