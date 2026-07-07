# CyberGuard

## Project Description

CyberGuard is a cybersecurity analytics workspace designed to help Security Operations Center (SOC) teams identify suspicious authentication behavior before user accounts are compromised. The project processes authentication logs, performs behavioral analysis, calculates user risk scores, stores processed data in a SQLite database, and visualizes insights through a Streamlit dashboard.

---

# Setup

## 1. Clone the Repository

```bash
git clone https://github.com/<YOUR-USERNAME>/SW2627-DataProduct-CyberGuard.git
cd SW2627-DataProduct-CyberGuard
```

## 2. Create a Virtual Environment

### macOS / Linux

```bash
python3 -m venv venv
```

### Windows

```bash
python -m venv venv
```

## 3. Activate the Virtual Environment

### macOS / Linux

```bash
source venv/bin/activate
```

### Windows (Command Prompt)

```cmd
venv\Scripts\activate
```

### Windows (PowerShell)

```powershell
venv\Scripts\Activate.ps1
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## 5. Verify the Installation

```bash
python -c "import pandas; print(pandas.__version__)"
```

---

# Project Structure

```
SW2627-DataProduct-CyberGuard/
│
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
├── scripts/
├── output/
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
```

### Directory Purpose

* **data/raw/** - Stores the original authentication log datasets without modification.
* **data/processed/** - Stores cleaned and transformed datasets ready for analysis.
* **notebooks/** - Contains Jupyter notebooks for data exploration, visualization, and experimentation.
* **scripts/** - Contains reusable Python scripts for data cleaning, feature engineering, risk scoring, and database operations.
* **output/** - Stores generated reports, charts, exported files, and dashboard outputs.

---

# Notes

* Environment variables are stored in a `.env` file.
* Copy `.env.example` to `.env` before running the project.
* Update the values inside `.env` with your own configuration.
* Do **not** commit the `.env` file or any sensitive credentials to Git.
* The virtual environment (`venv`) is excluded from version control using `.gitignore`.
* Project dependencies are captured in `requirements.txt` and can be installed using `pip install -r requirements.txt`.
