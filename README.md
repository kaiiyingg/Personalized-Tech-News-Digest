# Personalized-Tech-Digest

**Learning Stream: Your Personalized Tech Digest**

[![Build Status](https://github.com/YOUR_USERNAME/Personalized-Tech-News-Digest/actions/workflows/main.yml/badge.svg)](https://github.com/YOUR_USERNAME/Personalized-Tech-News-Digest/actions/workflows/main.yml)
*Replace `YOUR_USERNAME` with your GitHub username once the repo is created.*

## Table of Contents

* [Overview](#overview)
* [Features](#features)
* [Tech Stack](#tech-stack)
* [Architecture](#architecture)
* [DevOps & Best Practices](#devops--best-practices)
* [Local Setup & Development](#local-setup--development)
* [Deployment to AWS](#deployment-to-aws)
* [Future Enhancements](#future-enhancements)
* [License](#license)
* [Contact](#contact)

---

## Overview

In today's fast-paced tech landscape, information overload is a significant challenge for learners and professionals alike. The **Learning Stream: Your Personalized Tech Digest** is a cloud-native web application designed to combat this by providing a centralized, customizable, and intelligent feed of the latest tech news and learning resources tailored specifically to your interests.

This project empowers users to define their preferred content sources – such as RSS feeds from leading tech blogs, news sites, and even specific subreddits. Behind the scenes, an asynchronous, event-driven pipeline leverages **AWS Lambda** and **SQS** to ingest and process new content, ensuring a continuous flow of information without overwhelming the user. The core Flask API, containerized with **Docker** and deployed via **AWS Elastic Beanstalk**, serves the personalized digest, which is dynamically filtered based on user-defined interests stored securely in **AWS RDS (PostgreSQL)**.

Built with **DevOps best practices** at its core, the entire AWS infrastructure is defined and managed using **AWS CloudFormation (Infrastructure as Code)** for reproducibility and consistency. A robust **CI/CD pipeline** orchestrated by **GitHub Actions** automates code quality checks (linting, automated testing) and streamlines deployment, guaranteeing rapid and reliable updates.

---

## Features

* **Personalized Content Feed:** View the latest tech news and articles filtered by your custom interests (e.g., Serverless, AI/ML, DevOps, Python).
* **Customizable Sources:** Easily add, edit, and manage RSS feed URLs from your favorite tech websites and blogs.
* **User Authentication:** Secure login and registration system to manage individual user profiles and preferences.
* **Intelligent Ingestion:** An automated, serverless backend continuously pulls, parses, and processes new content from defined sources.
* **"Read Later" & Archiving:** Tools to save articles for deeper review and track already consumed content.
* **Interest Management:** Define and refine your specific tech interest keywords for precise content filtering.
* **Responsive Web UI:** A clean and intuitive web interface accessible from any browser on your laptop.

---

## Tech Stack

**Backend:**
* **Python 3.x:** Primary programming language.
* **Flask:** Lightweight web framework for the RESTful API and serving the frontend.

**Frontend:**
* **HTML5, CSS3, JavaScript:** For the user interface.

**Database:**
* **PostgreSQL:** Relational database for storing user data, source definitions, content metadata, and user interactions.
* **AWS RDS:** Managed PostgreSQL service in the cloud.

**Containerization:**
* **Docker:** For packaging the Flask application and its dependencies into isolated containers.
* **Docker Compose:** For orchestrating multi-container local development environments.

**Cloud Platform:**
* **Amazon Web Services (AWS):**
    * **AWS EC2 (via Elastic Beanstalk):** Virtual servers for the main application.
    * **AWS Elastic Beanstalk:** Platform as a Service (PaaS) for easy deployment and scaling of the Flask app.
    * **AWS Lambda:** Serverless compute for asynchronous content ingestion and processing.
    * **AWS SQS (Simple Queue Service):** Message queuing for decoupling ingestion steps and ensuring reliability.
    * **AWS S3 (Simple Storage Service):** Potentially for storing raw ingested content or static assets.
    * **AWS IAM (Identity and Access Management):** Securely manages access to AWS resources.
    * **AWS CloudWatch Events:** For scheduling recurring tasks (e.g., triggering content ingestion Lambdas).

**Infrastructure as Code (IaC):**
* **AWS CloudFormation:** To define, provision, and manage all AWS resources in a declarative YAML/JSON template.

**CI/CD & DevOps Tools:**
* **Git:** Version control system.
* **GitHub:** Remote repository hosting and integration with CI/CD.
* **GitHub Actions:** CI/CD platform for automating build, test, and deployment workflows.
* **Pylint:** Python linter for code quality and consistency checks.
* **Black:** Uncompromising Python code formatter.
* **Pytest:** Python testing framework for unit and integration tests.
* **Makefile:** For automating common development tasks (install, lint, test, format, build).

---

## Architecture

The system's architecture is divided into two main flows:

1.  **User Interaction Flow:**
    * Users access the web application through a browser.
    * The Flask application (hosted on AWS Elastic Beanstalk) handles user authentication and serves the personalized digest.
    * It interacts with AWS RDS (PostgreSQL) to retrieve user-specific data, sources, interests, and content.

2.  **Background Content Ingestion Flow:**
    * An **AWS CloudWatch Event** periodically triggers an **AWS Lambda function** (the Ingestion Orchestrator).
    * This Orchestrator Lambda reads user-defined sources from **AWS RDS** and sends messages to an **AWS SQS queue**.
    * Another **AWS Lambda function** (the Content Processor) is triggered by messages in the SQS queue.
    * The Content Processor fetches content from external sources (RSS feeds, etc.), parses it, filters it, and stores the processed metadata in **AWS RDS**.

This decoupled architecture ensures scalability, reliability, and cost-efficiency.

## Diagram:

## Demo Video:

---

## DevOps & Best Practices

This project rigorously applies the following DevOps principles:

* **Continuous Integration (CI):** Automated linting and testing (unit/integration) on every code commit via GitHub Actions to ensure code quality and catch issues early.
* **Continuous Delivery (CD):** Automated building, testing, and deployment of the application to AWS Elastic Beanstalk (and updates to CloudFormation stacks) through the GitHub Actions pipeline.
* **Infrastructure as Code (IaC):** All AWS infrastructure is defined in version-controlled AWS CloudFormation templates, ensuring environments are reproducible and eliminating "snowflake servers."
* **Containerization:** Using Docker to package the application, providing consistent environments from local development to cloud deployment.
* **Modularity:** The Flask application code is logically separated into distinct modules (e.g., `src/database`, `src/models`, `src/services`) for maintainability and clear responsibilities.
* **Automated Testing:** Comprehensive unit tests with Pytest and linting with Pylint are integrated into the development workflow and CI pipeline.
* **Dependency Management:** Strict use of `requirements.txt` for Python dependencies and a `Dockerfile` for container dependencies ensures reproducible builds.
* **Automated Tasks:** A `Makefile` streamlines common development and deployment commands, enforcing consistency.
* **Idempotence:** CloudFormation ensures that deploying the same infrastructure template multiple times results in the same desired state, making deployments robust.

---

## Local Setup & Development

To get the **Learning Stream: Your Personalized Tech Digest** running on your local machine:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/Personalized-Tech-News-Digest.git](https://github.com/YOUR_USERNAME/Personalized-Tech-News-Digest.git)
    cd Personalized-Tech-News-Digest
    ```
2.  **Create and activate a Python virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up local environment variables:**
    * Create a `.env` file in the project root (it's ignored by Git for security reasons).
    * Copy the content from `.env.example` and fill in your local database credentials.
    ```
    # .env example
    DB_NAME=learning_stream_db
    DB_USER=localuser
    DB_PASSWORD=localpassword
    DB_HOST=localhost
    DB_PORT=5432
    FLASK_APP=src/app.py
    ```
5.  **Run with Docker Compose (Recommended for local database):**
    * Ensure Docker Desktop is running.
    * This will spin up a local PostgreSQL database and your Flask application in containers.
    ```bash
    docker-compose up --build
    ```
    * The `docker-compose` command will also automatically create the necessary database tables (defined in `src/database/schema.sql` via `src/database/connection.py`).
6.  **Access the application:**
    * Open your web browser and navigate to `http://localhost:5000`.

*(Detailed instructions for individual Flask app run without Docker Compose, running tests, linting etc. can be added here or linked to a `CONTRIBUTING.md`)*

---

## Deployment to AWS

The entire application infrastructure and application code are deployed to AWS using **AWS CloudFormation** and automated via **GitHub Actions**.

1.  **AWS Account Setup:** Ensure you have an AWS account configured with appropriate IAM user/role credentials locally (e.g., via AWS CLI `aws configure`) and in your GitHub Actions secrets.
2.  **CloudFormation Deployment:**
    * The `infra/` directory contains the CloudFormation templates.
    * **Manual Deployment (First Time / Debugging):** You can manually deploy the stacks via the AWS CloudFormation console or AWS CLI:
        ```bash
        # Example for deploying network stack
        aws cloudformation deploy --template-file infra/network.yaml --stack-name learning-stream-network --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
        ```
    * **Automated Deployment (Recommended):** The GitHub Actions workflow (`.github/workflows/main.yml`) is configured to automatically deploy/update your CloudFormation stacks and application code upon pushes to the `main` branch, after successful tests and linting.
3.  **Application Deployment:** Your Flask application will be deployed to **AWS Elastic Beanstalk** as part of the CloudFormation stack, with its Docker image pushed to **AWS ECR**.
4.  **Access Deployed Application:** Once deployed, you will find the Elastic Beanstalk environment URL in the AWS Console.

*(Provide more specific AWS CLI commands for deploying each stack, if preferred over just mentioning automation.)*

---

## Future Enhancements

* **Advanced Content Filtering:** Implement more sophisticated content filtering based on user engagement, freshness decay, or personalized weighting.
* **Sentiment Analysis / Summarization:** Integrate AWS Comprehend or other NLP libraries to automatically summarize articles or gauge their sentiment.
* **Rich Content Sources:** Expand ingestion to include YouTube channels (via API), specific Twitter lists, or academic paper databases.
* **Email / Notification Digests:** Allow users to receive their personalized digest via email (AWS SES) or other notification channels (AWS SNS).
* **"Hot Topics" / Trending Section:** Develop algorithms to identify and display trending tech topics based on content volume and recency.
* **UI/UX Improvements:** Enhance the frontend with more dynamic components using a modern JavaScript framework (React/Vue/Angular).

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Contact

- 📧 Email: [chongkaiying578@gmail.com](mailto:chongkaiying578@gmail.com)  
- 📱 Phone: +65 8917 2864  
- 💼 LinkedIn: [linkedin.com/in/kai-ying-907bb6178](https://linkedin.com/in/kai-ying-907bb6178)

---