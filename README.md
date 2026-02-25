# BiasGuard: Bias-Aware Federated Learning Framework for ICU Analytics

## 📌 Project Overview
**BiasGuard** is a privacy-preserving framework designed to detect and mitigate algorithmic bias in distributed healthcare networks.

In traditional ICU analytics, patient data is centralized, creating privacy risks and "data silos." Federated Learning (FL) solves this by training models locally at each hospital. However, if a specific hospital has biased data (e.g., higher mortality rates for a specific demographic), this bias can corrupt the global model.

**This Prototype (IPD Phase)** demonstrates a "Vertical Slice" of the solution:
1.  **Federated Simulation:** Simulates a network with two hospital nodes (Hospital A & Hospital B).
2.  **Real-Time Bias Engine:** Intercepts model updates *during training* to check for Demographic Parity violations.
3.  **Admin Command Center:** A React-based dashboard for IT administrators to monitor network health and fairness compliance in real-time.

---

## 🛠️ Tech Stack

### **Backend (The Core Framework)**
* **Python 3.9+**
* **FastAPI:** For the REST API and dashboard communication.
* **Scikit-Learn:** For the local mortality prediction models (Logistic Regression).
* **NumPy/Pandas:** For data manipulation and bias metric calculation.

### **Frontend (The Dashboard)**
* **React.js:** For the dynamic user interface.
* **Tailwind CSS:** For the "Midnight Clinical" professional styling.
* **Recharts:** For real-time data visualization.
* **Axios:** For API polling.

---

## 🚀 How to Run the Project

### **Prerequisites**
* Python 3.x installed.
* Node.js & npm installed.

### **Step 1: Setup the Backend**
1.  Open a terminal and navigate to the `backend` folder:
    ```bash
    cd backend
    ```
2.  Install the required Python libraries:
    ```bash
    pip install pandas numpy scikit-learn fastapi uvicorn
    ```   
4.  **Start the Server:**
    ```bash
    uvicorn api:app --reload
    ```
    *You should see: `Uvicorn running on http://127.0.0.1:8000`*

### **Step 2: Setup the Frontend**
1.  Open a **new** terminal window and navigate to the `frontend` folder:
    ```bash
    cd frontend
    ```
2.  Install the React dependencies:
    ```bash
    npm install
    ```
    *(Note: If you haven't installed Tailwind yet, follow the setup in `frontend/tailwind.config.js`)*
3.  **Launch the Dashboard:**
    ```bash
    npm start
    ```
    *This will automatically open `http://localhost:3000` in your browser.*

---

## 🧪 The Demo Scenario

When you run the project, the system simulates a Federated Learning cycle:

1.  **Initialization:** The Global Model starts with 60% accuracy.
2.  **Rounds 1-2 (Normal Operation):**
    * **Hospital A** (Fair Data) sends updates.
    * **Hospital B** (Biased Data) sends updates, but the bias is initially low.
    * *Dashboard Status:* **"System Secure" (Green)**.
3.  **Round 3+ (The Attack):**
    * **Hospital B** begins submitting data that is heavily biased against Senior Patients (Age > 65).
    * **The BiasGuard Engine** calculates a Demographic Parity Score > 0.15.
    * *Dashboard Status:* **"VIOLATION DETECTED" (Red)**.
    * **Action:** The system automatically **Rejects** the update from Hospital B to protect the global model.