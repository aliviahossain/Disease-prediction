# 🏥 Disease Prediction Setup Guide

Step-by-step instructions to set up and run the Disease Prediction web application on a local machine.

---

## Prerequisites

Ensure the following are installed on your system:

- Python 3.8 or higher  
- pip (Python package manager)  
- Git  

Verify installations using:

```bash
python --version
pip --version
git --version
```

---

## 1. Clone the Repository

Clone the repository and move into the project directory:

```bash
git clone https://github.com/your-username/Disease-prediction.git
cd Disease-prediction
```

---

## 2. Create and Activate Virtual Environment (Recommended)

Using a virtual environment helps avoid dependency conflicts.

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

If a `requirements.txt` file is present, install dependencies using:

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not available, install dependencies manually:

```bash
pip install flask numpy pandas scikit-learn matplotlib seaborn
```

---

## 4. Run the Application

Run the main application file using one of the following commands:

```bash
python app.py
```

or

```bash
python main.py
```

If the project uses Flask CLI, run:

```bash
flask run
```

---

## 5. Access the Web Application

After starting the application, open your browser and visit:

```
http://127.0.0.1:5000/
```

You should now see the Disease Prediction web application running locally.

---

## Troubleshooting

### ModuleNotFoundError

- Ensure the virtual environment is activated
- Reinstall dependencies:

```bash
pip install -r requirements.txt
```

### Port Already in Use

- Stop any other service using port 5000
- Or change the port number in the Flask app

### Virtual Environment Activation Issues (Windows)

- Open PowerShell as Administrator
- Run:

```bash
Set-ExecutionPolicy RemoteSigned
```

---

## Deactivate Virtual Environment

When finished, deactivate the virtual environment:

```bash
deactivate
```

---

## Notes

- This setup works on Windows, macOS, and Linux
- Ensure Python is added to the system PATH
- Follow the steps in the given order for best results

---

## Need Help?

If you encounter any issues not covered in this guide, please:

- Check the project's GitHub issues page
- Review the project documentation
- Ensure all prerequisites are correctly installed
