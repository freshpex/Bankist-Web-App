# Bank Web Application Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Configuration](#configuration)
4. [Architecture](#architecture)
    - [Overview](#overview)
    - [Database Schema](#database-schema)
5. [Usage](#usage)
    - [Running the Application](#running-the-application)
    - [Accessing the Web Interface](#accessing-the-web-interface)
6. [Models](#models)
    - [User](#user)
    - [Account](#account)
    - [Transaction](#transaction)
    - [Loan](#loan)
    - [Receipt](#receipt)
    - [Card](#card)
7. [Scripts](#scripts)
    - [create_db.py](#create_dbpy)
8. [Contributing](#contributing)
9. [License](#license)

## 1. Introduction<a name="introduction"></a>

This is a web application that provides users with a simplified and digital banking experience. It offers features such as instant transfers, loans, account management, and more.

## 2. Features<a name="features"></a>

- **Digital Banking:**
  - 100% digital banking for managing finances anytime, anywhere.
- **Investment:**
  - Users can invest and watch their money grow with the help of financial advisors.
- **Free Debit Card:**
  - Open an account and get a free debit card for cashless transactions.
- **Instant Operations:**
  - Instant transfers, instant loans, and instant account closing.

## 3. Getting Started<a name="getting-started"></a>

### Prerequisites<a name="prerequisites"></a>

- Python 3.x
- Flask
- SQLite

### Installation<a name="installation"></a>

1. Clone the repository: `git clone https://github.com/your-username/bankist.git`
2. Navigate to the project directory: `cd bankist`
3. Install dependencies: `pip install -r requirements.txt`

### Configuration<a name="configuration"></a>

- Configure the database URI in `create_db.py`.
- Set environment variables for sensitive information.

## 4. Architecture<a name="architecture"></a>

### Overview<a name="overview"></a>

It is built using Flask, a Python web framework. The application follows a client-server architecture with a SQLite database for data storage.

### Database Schema<a name="database-schema"></a>

The application uses the following database models:

- User
- Account
- Transaction
- Loan
- Receipt
- Card

## 5. Usage<a name="usage"></a>

### Running the Application<a name="running-the-application"></a>

Execute the following command to install all dependencies

```bash
pip install requirements.txt
```


Execute the following command to run the application:

```bash
python app.py
```

### Accessing the Web Interface<a name="accessing-the-web-interface"></a>

Open a web browser and navigate to `http://localhost:5000` to access the Bankist web interface.

## 6. Models<a name="models"></a>

### User<a name="user"></a>

- Fields:
  - id
  - email
  - firstname
  - lastname
  - username
  - gender
  - privacy_enabled
  - notification_enabled
  - profile_image
  - account_type
  - accounts
  - password

### Account<a name="account"></a>

- Fields:
  - id
  - account_number
  - user_id
  - account_type
  - balance

### Transaction<a name="transaction"></a>

- Fields:
  - id
  - date
  - description
  - amount
  - timestamp
  - account_number
  - user_id

### Loan<a name="loan"></a>

- Fields:
  - id
  - date
  - account_id
  - amount
  - status

### Receipt<a name="receipt"></a>

- Fields:
  - id
  - transaction_id
  - amount
  - description
  - destination_country
  - currency

### Card<a name="card"></a>

- Fields:
  - id
  - card_number
  - cvv
  - expiration_date
  - cardholder_name
  - card_type
  - user_id

## 7. Scripts<a name="scripts"></a>

### create_db.py<a name="create_dbpy"></a>

The `create_db.py` script initializes and creates the necessary database tables.

Usage:

```bash
python create_db.py
```

## 8. Contributing<a name="contributing"></a>

Contributions are welcome! Follow the guidelines in the [CONTRIBUTING.md](CONTRIBUTING.md) file.

## 9. License<a name="license"></a>

This project is licensed under the [MIT License](LICENSE).
