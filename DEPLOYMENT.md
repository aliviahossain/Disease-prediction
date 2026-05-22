# 🚀 Deployment Guide

This repository is optimized for containerized environments. This guide provides comprehensive, verified instructions for running the primary **Flask Web Application** locally via Docker Compose and deploying it to production on **Render**.

---

## 🔗 Live Production Demo
**The application is deployed live on the cloud. You can access the production environment here:**
👉 **[https://disease-prediction-nwnu.onrender.com]**

---

## 🛠️ Local Deployment (Using Docker Compose)

Using Docker ensures the application runs inside an isolated container with identical system dependencies, mitigating platform-specific compatibility issues.

### Prerequisites
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) for your operating system.
- Ensure the Docker Desktop daemon is running before executing commands.

### Steps to Run Locally

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/Disease-prediction.git](https://github.com/YOUR_USERNAME/Disease-prediction.git)
   cd Disease-prediction

2. **Configure Environment Variables:**
Create a .env file in the root directory. The application requires a secure runtime token and a Google AI Studio credential to communicate with the Gemini analytics layer:

   ```bash 
   SECRET_KEY=770b6249aeb91b030e9651f8a3b6456ad8fc6249631b2d522105b43c0d362c26
   GEMINI_API_KEY=your_actual_google_ai_studio_api_key_here
   ```
      **Note:** The .env file is explicitly included in .gitignore and .dockerignore to prevent security credentials from being pushed to public source control.

3. **Build and Boot the Container:**
Execute the following command to download the optimized baseline Python environment, install required machine learning dependencies, and boot the Gunicorn server:

   ```Bash
   docker compose up --build
   ```
4. **Access the Application:**
Once the terminal logs confirm that the Gunicorn master process has booted and is listening, open your browser and navigate to:
👉 http://localhost:5001

5. **Teardown:**
To safely shut down the container and release the network ports, press Ctrl + C in your terminal or run:

   ```Bash
   docker compose down
   ```

### 🌐 Production Deployment (On Render)
The runtime environment is configured to deploy seamlessly to Render as a Web Service utilizing the repository's native Dockerfile.

**Step-by-Step Render Setup**
1. **Connect Repository:**

   - Log into your Render Dashboard.

   - Click New + in the top right and select Web Service.

   - Connect your GitHub repository fork.

2. **Base Service Configurations:**

   - Name: disease-prediction-app (or your preferred identifier)

   - Branch: Select your active deployment/feature branch.

   - Region: Select the region closest to your target audience.

   - Runtime / Language: Select Docker (This is mandatory. It forces Render to compile your optimized production Dockerfile rather than using standard Python runtimes).

   - Instance Type: Select Free.

3. 3. **Inject Runtime Environment Variables:**
   Scroll down, click **Add Environment Variable**, and insert the following required configuration tokens:

   | Key | Value | Description |
   | :--- | :--- | :--- |
   | `SECRET_KEY` | `770b6249aeb91b030e9651f8a3b6456ad8fc6249631b2d522105b43c0d362c26` | Used by the `SecurityValidator` framework to secure application traffic. |
   | `GEMINI_API_KEY` | `AIzaSy...` | Your individual key generated via [Google AI Studio](https://aistudio.google.com/). |

4. **Execution and Monitoring:**

   - Click Deploy Web Service.

   - Render's multi-port scanner will automatically detect the EXPOSE 5001 flag from the Dockerfile and securely map public incoming HTTP traffic directly to the Gunicorn server process.

   - Once the logs stream lists a green Live status badge, your public URL will be accessible at the top of the service dashboard.