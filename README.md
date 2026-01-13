# Curizen Chatbot

A sophisticated chatbot application that integrates with Gmail, Google Calendar, and uses Cassandra for vector storage. This project leverages OpenAI's language models and LangChain framework to provide intelligent responses and manage various tasks.

## Features

- Gmail integration for email management
- Google Calendar integration for scheduling
- Vector storage using Cassandra DB
- OpenAI integration for natural language processing
- FastAPI backend for API endpoints
- LangChain integration for advanced conversation management

## Prerequisites

- Python 3.10 or higher
- Astra DB account (for Cassandra vector storage)
- Google Cloud Platform account with Gmail and Calendar API access
- OpenAI API key
- LangChain API key

## Environment Variables

The following environment variables need to be set:

```env
LANGCHAIN_API_KEY=your_langchain_api_key
OPENAI_API_KEY=your_openai_api_key
ASTRA_DB_APPLICATION_TOKEN=your_astra_db_token
ASTRA_DB_ID=your_astra_db_id
```

## Installation

1. Clone the repository
2. Create and activate a virtual environment:
```bash
python -m venv curizen_render
source curizen_render/bin/activate  # On Windows: .\curizen_render\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Required Dependencies

The project requires several Python packages:
- LangChain ecosystem (langchain, langchain-community, langchain-text-splitters)
- Vector store: faiss-cpu, cassio
- Google API libraries (google-api-python-client, google-auth-oauthlib)
- Web framework: FastAPI, uvicorn
- Document processing: unstructured, docx2txt
- Other utilities: beautifulsoup4, pytz, tzdata

## Authentication

1. Set up Google Cloud Platform credentials:
   - Create a project in Google Cloud Console
   - Enable Gmail and Calendar APIs
   - Download credentials.json and place it in the project root
   - Run the application to generate token.json for authentication

2. Configure Astra DB:
   - Create an Astra DB account
   - Set up a database and obtain the application token
   - Configure the environment variables with your Astra DB credentials

## Usage

1. Ensure all environment variables are properly set
2. Start the FastAPI server:
```bash
uvicorn main:app --reload
```

3. The application will handle:
   - Email management through Gmail integration
   - Calendar scheduling and management
   - Vector storage and retrieval using Cassandra
   - Natural language processing using OpenAI

## Project Structure

- `main.py`: Main application file with FastAPI setup and core logic
- `requirements.txt`: List of Python dependencies
- `credentials.json`: Google Cloud Platform credentials
- `token.json`: Generated authentication token
- `.env`: Environment variables (not included in repository)
