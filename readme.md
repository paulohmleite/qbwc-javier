# Microservice Installation and Execution Guide

This guide explains how to configure and run the microservice using **Python 3.10**.

## Requirements

- [Python 3.10](https://www.python.org/downloads/) installed.
     

## Configuration Steps

### 1. Create a Virtual Environment with Python 3.10

Open the terminal or Command Prompt and execute:

```bash
python -m venv venv
```

### 2. Activate the Virtual Environment

On Windows, execute:

```bash
.\venv\Scripts\activate
```

### 3. Install the Dependencies

Execute:

```bash
pip install -r requirements.txt
```

### 4. Configure the Environment Variables at the Beginning of the microservice File

```python
# Change these values to match your QuickBooks Desktop credentials
QB_USER = "Admin"
QB_PASSWORD = "admin"
COMPANY_NAME = "D:\\FV-DOC\\sample_wholesale-distribution business.QBW"
```


### 5. Run the Microservice

Execute:

```bash
python microservice.py
```

## TODO

- [ ] You need to configure the sample of salesorder to use values from your QuickBooks Desktop.
- [ ] Solve the TODOs in the code.
