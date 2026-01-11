# Disease Prediction Setup Guide

This guide will help you set up the Disease Prediction web application on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8 or higher**
  - Download from: https://www.python.org/downloads/
  - Verify installation: `python --version`

- **Git**
  - Download from: https://git-scm.com/downloads
  - Verify installation: `git --version`

- **Virtual Environment (venv)** - Usually comes with Python

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/aliviahossain/Disease-prediction.git
cd Disease-prediction
```

### 2. Create a Virtual Environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist, install the main dependencies:
```bash
pip install flask
pip install scikit-learn
pip install pandas
pip install numpy
```

### 4. Run the Application

**Using Flask Development Server:**
```bash
python app.py
```

Or using Flask CLI:
```bash
python -m flask run
```

### 5. Access the Application

Open your web browser and navigate to:
```
http://localhost:5000
```

## Troubleshooting

### Issue: Command 'python' not found
**Solution:** Use `python3` instead of `python`
```bash
python3 -m venv venv
python3 app.py
```

### Issue: Module not found error
**Solution:** Ensure you're in the virtual environment and all dependencies are installed
```bash
pip install -r requirements.txt
```

### Issue: Port 5000 already in use
**Solution:** Run Flask on a different port
```bash
flask run --port 5001
```

## Project Structure

- `backend/` - Backend Flask application
- `app.py` - Main Flask application file  
- `requirements.txt` - Python dependencies
- `README.md` - Project documentation

## Development Notes

- The application uses **Bayes' Theorem** for disease prediction
- Default **Port:** 5000
- Ensure you have Python 3.8+ for compatibility

## Deactivate Virtual Environment

When you're done developing:
```bash
deactivate
```

## Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Project README](./README.md)
- [Contributing Guide](./CONTRIBUTING.md)

## Need Help?

If you encounter any issues:
1. Check the [Issues](https://github.com/aliviahossain/Disease-prediction/issues) page
2. Review the [Contributing Guidelines](./CONTRIBUTING.md)
3. Open a new issue with detailed information

Happy coding! 🚀
