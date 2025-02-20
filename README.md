# TalentSync Project

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI Version](https://img.shields.io/badge/FastAPI-0.115.8+-blue.svg)](https://fastapi.tiangolo.com/)

## Description

Sync-Resume is a FastAPI application  designed to facilitate the parsing and analysis of resumes as a part of the Talent Sync project. The primary goal is to extract structured information from resumes and store the data in both traditional databases and vector stores. This enables the efficient matching of candidates' skills, experience, and qualifications with the most relevant job opportunities.

## Entrypoint File

The entrypoint of this project is located in the `main.py` file. This file initializes the FastAPI application and defines the routes for handling resume parsing and analysis.

## Features

* Robust resume parsing capabilities to extract structured information
* Storage of parsed data in traditional databases and vector stores
* Efficient matching of candidates with job opportunities based on their skills, experience, and qualifications

## Technology Stack

* FastAPI for building the web application
* Langchain & Langgraph for Agent Orchestration
* Unstrcutured for Document Parsing

## Getting Started

### Prerequisites

* Python 3.11+
* uv

### Installation

1. Clone the repository to your local machine.
2. Install the required dependencies using `uv sync`.
3. Run the application using `uvicorn main:app --host 0.0.0.0 --port 8000`.

### Usage

Use OpenAPI Client in the Swagger docs to test the deployment. The API documentation will be available at `http://localhost:8000/docs`.

## API Endpoints

The API endpoints for this project are defined in the `main.py` file. You can explore the available endpoints and their usage by visiting the API documentation.

## Contributing

Contributions to this project are welcome. If you'd like to contribute, please fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.
