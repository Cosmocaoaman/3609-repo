# Jacaranda Talk Forum System

A campus forum system built with Django and React with integrated Mailjet email service.

## Project Overview

**Jacaranda Talk** is a comprehensive campus forum system designed to facilitate free and open communication within academic communities. The platform provides a modern, user-friendly interface that empowers students and faculty to engage in unrestricted discussions, share resources, and build meaningful connections while maintaining privacy and security through advanced anonymous posting capabilities.

### Objectives
- Create a secure and scalable forum platform for campus communities
- Implement user authentication and role-based access control
- Provide content management features including posting, commenting, and moderation
- Enable anonymous posting capabilities for sensitive discussions
- Offer advanced search and categorization features

### Main Features
- **User Management**: Registration, authentication, profile management, and role-based permissions
- **Content Creation**: Thread posting, commenting, editing, and deletion with anonymous options
- **Anonymous System**: Secure anonymous posting and commenting capabilities for sensitive discussions
- **Search & Discovery**: Full-text search with tag filtering and category organization
- **Administrative Tools**: User management, content moderation, and system analytics
- **Email Integration**: Automated notifications via Mailjet service
- **Responsive Design**: Mobile-friendly interface with modern UI/UX

## Quick Start

### 📋 Manual Setup

#### 1. Environment Setup
```bash
pip install -r requirements.txt
cd frontend && npm install
```

#### 2. Email Service Configuration (Mailjet)

**Quick Setup**:
1. Create a file named `.env` in the project root directory
2. Open `env_template.txt` and copy all contents
3. Paste the contents into the new `.env` file
4. The `.env` file is already configured with working Mailjet credentials

**If you want to use your own Mailjet account**:
1. Register at https://app.mailjet.com/
2. Create API credentials (Account settings → API keys)
3. Replace the values in `.env` with your own credentials:
   ```
   MAILJET_API_KEY=your_api_key
   MAILJET_API_SECRET=your_api_secret
   MAILJET_FROM_EMAIL=your_email@domain.com
   MAILJET_FROM_NAME=Jacaranda Talk
   EMAIL_ENCRYPTION_KEY=your_encryption_key
   ```
4. Generate a new encryption key if needed:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

#### Email Delivery Tips
**Recommended Email Providers**: For best results, use Gmail or Outlook email addresses. These providers have better email deliverability rates with Mailjet.

**If you don't receive the verification code**:
1. Check your spam/junk folder - the OTP email may be filtered there
2. Wait up to 2-3 minutes for email delivery
3. Try requesting a new code after the 60-second cooldown period
4. Ensure your email address is correctly typed during registration

#### File-based Email (Development Only)
If Mailjet is not configured or the API send fails, the system automatically falls back to the file-based backend (emails are written to the `emails/` directory).

#### 3. Database Setup
```bash
python manage.py migrate
python manage.py loaddata fixtures/current_data.json
```
#### 4. Start Services
```bash
python manage.py runserver
cd frontend && npm run dev
```

## Database Sharing

**Export**: `python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission -o fixtures/current_data.json`
**Import**: `python manage.py loaddata fixtures/current_data.json`

## Tech Stack
- **Backend**: Django 5.2.6, Django REST Framework
- **Frontend**: React, TypeScript, Vite
- **Database**: SQLite
## External Libraries Used
- React (v19.1.1) – Component-based UI library for building the SPA interface.
- React DOM (v19.1.1) – DOM renderer for React components.
- React Router DOM (v7.9.3) – Client-side routing and protected route handling.
- Bootstrap (v5.3.8) – Responsive layout and pre-styled UI components.
- TypeScript (v5.8.3) – Sthttps://github.sydney.edu.au/2025S2-INTERNET-SOFTWARE-PLATFORM/Fri-13-16-01/blob/main/README.mdatic type checking for safer, maintainable front-end code.
- Vite (v7.1.7) – Fast dev server and build tool with HMR and optimized bundling.
- ESLint (v9.36.0) – Linting and code-quality enforcement for JavaScript/TypeScript.

## Testing Guide and Coverage Reports

This project uses Django testing framework for backend testing with a goal of achieving **85%+ test coverage**. Tests include:

- **Model Tests** (forum/models.py)
- **API View Tests** (api/views.py)
- **Serializer Tests** (api/serializers.py)
- **Authentication Tests** (forum/authentication.py)
- **Email Service Tests** (forum/email_service.py)
- **Forum View Tests** (forum/views.py)

## Test Environment Setup

### 1. Install Dependencies

```bash
# Install coverage tool
pip install coverage

# Ensure all test dependencies are installed
pip install -r requirements.txt
```

### 2. Test Configuration

The project uses `test_config.py` for test environment configuration:

```python
# test_config.py provides:
- In-memory database configuration
- Test-specific cache settings
- Email backend configuration
- Logging configuration
- Temporary directory settings
```

## Running Tests

### 1. Using Test Runner Script

```bash
# Run all tests and generate coverage reports
python run_tests.py
```

This script will:
- Run all test cases
- Generate text format coverage report
- Generate HTML format coverage report
- Check if 85% coverage threshold is met

### 2. Manual Test Execution

```bash
# Run all tests
python manage.py test

# Run specific module tests
python manage.py test forum.tests
python manage.py test api.tests
python manage.py test api.serializer_tests

# Run specific test classes
python manage.py test forum.tests.UserModelTest
python manage.py test api.tests.AuthenticationAPITest

# Run specific test methods
python manage.py test forum.tests.UserModelTest.test_user_creation
```

### 3. Using Coverage Tool

```bash
# Run tests and collect coverage data
coverage run --source=forum,api manage.py test forum.tests api.tests api.serializer_tests --verbosity=2

# Generate text report
coverage report --show-missing

# Generate HTML report
coverage html

# Generate XML report (for CI/CD)
coverage xml
```

## Generating Coverage Reports

### 1. Text Format Report

```bash
coverage report --show-missing
```

### 2. HTML Format Report

```bash
coverage html
```

- Reports saved in `htmlcov/` directory
- Open `htmlcov/index.html` to view detailed report
- Click on file names to see specific code coverage
- Red lines indicate uncovered code, green lines indicate covered code

## We would like to note that the commits from 63bc0b6 to the latest commit were all made for Assignment 3 deployment and security-related improvements. However, we forgot to use a separate branch for these changes, so they were pushed directly to the main branch.
