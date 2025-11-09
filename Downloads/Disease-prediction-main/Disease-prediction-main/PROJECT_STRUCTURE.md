# 📂 Project Structure Explained: A Beginner's Guide

Hello! Welcome to the Disease Prediction project. If you're new to web development, all these files and folders might look confusing. Don't worry! This guide is here to explain the purpose of every file.

Think of this project like building a car:
-   The **Python/Flask** code is the **engine** (it does all the work).
-   The **HTML** is the **car's body and seats** (the structure you see and interact with).
-   The **CSS** is the **paint job and design** (making it look good).
-   The **JavaScript** is the **dashboard electronics** (like the radio and power windows).

Let's break it down file by file.

---

### The Core Logic

#### 📄 `app.py`
* **WHAT**: This is the main brain of our web application. It's a Python script that uses the Flask framework to run a web server.
* **WHY**: It acts as the traffic controller. It listens for requests from a user's web browser (like when you click "Calculate") and connects the user interface (the website) with our powerful calculator logic in the backend.
* **HOW**: When you run `python app.py`, it starts a local web server. It loads the `index.html` file to show you the webpage. When you submit data through the form, this script catches that data, sends it to `calculator.py` for processing, gets the result back, and then reloads the webpage to display the answer.

#### 📁 `src/`
This folder is where we keep the core, essential logic of our application.

#### 📄 `src/calculator.py`
* **WHAT**: A Python script that contains the pure mathematical logic for Bayes' Theorem.
* **WHY**: By separating the math from the web server code, our project becomes much cleaner and easier to manage. This principle is called **"Separation of Concerns."** It allows us to test our calculator's accuracy without needing to run the whole website.
* **HOW**: This file likely contains a function that takes numbers as input (like prior probability, sensitivity, etc.), performs the Bayes' Theorem calculation, and returns the final probability. The `app.py` file calls this function whenever it needs to do the math.

---

### 🖼️ The Frontend (What You See in the Browser)

#### 📁 `templates/`
This is the standard folder where Flask looks for HTML files. They are called "templates" because they are like fill-in-the-blank documents.

#### 📄 `templates/index.html`
* **WHAT**: The HTML file that defines the structure of our webpage.
* **WHY**: This file builds the skeleton of the site: the title, the input boxes for the user to enter numbers, the "Calculate" button, and the spot where the final answer will appear.
* **HOW**: It's a standard HTML file, but with special placeholders (like `{{ result }}`). Flask's template engine replaces these placeholders with actual data from our Python code before sending the final page to the user's browser.

#### 📁 `static/`
This folder holds "static" files, meaning they don't change. The web server sends them directly to the user's browser without any processing. This is where we put our CSS and JavaScript.

#### 📄 `static/style.css`
* **WHAT**: A Cascading Style Sheet (CSS) file.
* **WHY**: To make our website look beautiful! HTML provides the structure, but CSS provides the style—colors, fonts, spacing, and layout. Separating style from structure is a core principle of modern web development.
* **HOW**: The `index.html` file contains a link to this `style.css` file. When a browser loads the HTML, it sees the link, fetches the CSS file, and applies the styling rules to all the HTML elements.

#### 📄 `static/script.js`
* **WHAT**: A JavaScript file.
* **WHY**: To make the webpage interactive and user-friendly. For example, it could be used to instantly check if a user entered a valid number in a box or to show a loading spinner while the calculation is running.
* **HOW**: Just like the CSS file, `index.html` includes a link to this script. The JavaScript code runs directly inside the user's browser, allowing it to manipulate the webpage in real-time without needing to constantly ask the server for updates.

---

### 💾 Data and Testing

#### 📄 `hospital_data.csv`
* **WHAT**: A CSV (Comma-Separated Values) file, which is a simple, plain-text format for storing spreadsheet-like data.
* **WHY**: This file holds the sample data our calculator might use. Keeping data separate from code is great because you can easily update the dataset without having to change a single line of code!
* **HOW**: Our Python script can open and read this file to pull in the numbers needed for the probability calculations.

#### 📁 `tests/`
This folder contains automated tests to make sure our code works correctly.

#### 📄 `tests/test_calculator.py` & `test_integration.py`
* **WHAT**: Python scripts that automatically test our code's functionality. `test_calculator.py` is a **unit test** (tests one small piece) and `test_integration.py` is an **integration test** (tests how multiple pieces work together).
* **WHY**: To ensure our calculator is accurate and reliable. When we make changes to the code, we can run these tests to instantly check if we broke anything. This gives us confidence that our app works as expected.
* **HOW**: Each test script defines a scenario. For example, a test might provide the calculator with known inputs and then check if the output matches the pre-calculated, correct answer. If it doesn't match, the test fails, alerting us to a bug.

---

### 📜 Project Management & Community Files

These files don't run, but they are very important for explaining the project to other humans.

* **`README.md`**: The front page of the project. It tells visitors what the project does, why it's useful, and how to get it running.
* **`LICENSE`**: The legal document that explains how others are allowed to use your code. The MIT License is very popular because it's simple and allows people to do almost anything with the code.
* **`.gitignore`**: A list of files and folders that Git (our version control system) should ignore. This is used to prevent temporary files or secret information from being saved in the project's history.
* **`CONTRIBUTING.md`**: A guide for other developers who want to contribute to the project. It explains the rules and the process for submitting changes.
* **`CODE_OF_CONDUCT.md`**: Sets the rules for respectful and professional behavior within the project community, ensuring it's a welcoming space for everyone.