# Mistra Project

This guide will help you set up and run the Mistra project locally on your machine.

## Prerequisites

Make sure you have the following installed on your system:

* Python (recommended: version 3.8 or higher)
* Git

## Setup Instructions

Follow the steps below to clone the repository and set up the project environment:

```bash
# Clone the repository
git clone https://github.com/divorced-dad/mistra

# Navigate into the project directory
cd mistra

# Create a virtual environment
py -m venv venv

# Activate the virtual environment
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Start the development server
py manage.py runserver
```

## Accessing the Application

Once the server is running, you can access the application by visiting `http://127.0.0.1:8000/` in your web browser.

---


## Report

campo dottore su TestExecutions
texto>text

