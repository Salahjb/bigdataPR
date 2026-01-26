# Big Data & BI Analysis of Scientific Research
### Capstone Project | Architecture Big Data & BI

## 📌 Project Overview
This project implements a complete Big Data pipeline to collect, store, analyze, and visualize scientific research trends. It automates the extraction of data from academic repositories (IEEE Xplore), processes it using distributed computing, and presents insights via a BI dashboard.

**Objective:** Build a decision-support system to identify research trends, top authors, and emerging topics ("Weak Signals").

---

## 🏗️ Technical Architecture

### 1. Data Collection (Ingestion)
* **Source:** IEEE Xplore (Dynamic Single Page Application)
* **Framework:** **Scrapy** (Python)
* **Bypass Strategy:** **Selenium** with `undetected-chromedriver` (to bypass F5/APM security & Captchas)
* **Output:** Structured JSON documents.

### 2. Storage Layer (Data Lake)
* **Operational DB:** **MongoDB** (NoSQL) - Storing unstructured JSON articles.
* **Batch Storage:** **Hadoop HDFS** - Distributed file system for heavy processing.

### 3. Processing & Analysis
* **Engine:** **Apache Spark** (PySpark)
* **Techniques:**
    * Data Cleaning & Normalization.
    * **NLP:** TF-IDF for keyword extraction.
    * **Machine Learning:** LDA (Latent Dirichlet Allocation) for Topic Modeling.

### 4. Visualization (BI)
* **Frontend:** Streamlit
* **Insights:** Word Clouds, Co-authorship Graphs, Temporal Trends.

---

## 🛠️ Installation & Setup

### Prerequisites
* Python 3.9+
* Google Chrome (Latest Stable Version)
* MongoDB (Local or Docker)
* Apache Spark (for Phase 3)

### 1. Environment Setup
```bash
# Clone the repository
git clone [https://github.com/Salahjb/bigdataPR.git](https://github.com/Salahjb/bigdataPR.git)
cd bigdataPR

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install scrapy selenium undetected-chromedriver pymongo pyspark
