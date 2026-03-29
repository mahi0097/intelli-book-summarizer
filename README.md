# Intelligent Book Summarization

Intelligent Book Summarization is a Streamlit-based application for uploading books, extracting text, generating AI summaries, managing summary versions, and reviewing usage through an admin dashboard. The project combines a Streamlit frontend, Python backend services, MongoDB persistence, and an AI summarization layer that prefers Gemini 2.5 Flash with a local Hugging Face fallback.

## Overview

The application is designed to support a full user workflow:

- user registration and login
- book upload from `TXT`, `PDF`, and `DOCX`
- text extraction and storage
- AI summary generation from uploaded books or pasted text
- version history, comparison, favorites, and restoration
- export options for summaries
- admin-only monitoring and user management

## Key Features

- AI summarization using Gemini 2.5 Flash when `GEMINI_API_KEY` is configured
- fallback summarization support using a local Hugging Face BART model
- direct text paste summarization for quick workflows
- file upload and extraction for `txt`, `pdf`, and `docx`
- summary length, style, and tone controls
- summary versioning and comparison tools
- favorites and archive flows for summaries
- admin dashboard with user and system visibility
- MongoDB-backed user, book, summary, and progress data
- automated tests for unit, integration, security, and performance coverage

## Tech Stack

- Frontend: Streamlit
- Backend: Python
- Database: MongoDB
- AI Providers:
  - Gemini 2.5 Flash via Google Generative Language API
  - Hugging Face `facebook/bart-base` fallback
- Authentication: bcrypt + JWT
- Testing: pytest, pytest-cov, pytest-mock, pytest-asyncio, locust

## Project Structure

```text
Intelligent_Book_Summarization/
├── app.py
├── backend/
│   ├── auth.py
│   ├── summary_orchestrator.py
│   ├── text_extractor.py
│   ├── models/
│   │   └── summarizer.py
│   ├── exporters/
│   └── api/
├── frontend/
│   ├── auth.py
│   ├── dashboard.py
│   ├── upload.py
│   ├── generate_summary.py
│   ├── mybooks.py
│   ├── summaries.py
│   ├── SummaryHistory.py
│   ├── summary_compare.py
│   └── admin_dashboard.py
├── utils/
│   ├── database.py
│   ├── error_handler.py
│   ├── formatters.py
│   ├── stats.py
│   └── validators.py
├── config/
│   └── settings.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   ├── performance/
│   └── system/
└── requirements.txt
```

## How It Works

### User Flow

1. Register or log in.
2. Upload a book or paste text directly.
3. Extract and store text content.
4. Generate a summary with selected options.
5. Save, compare, export, or favorite summary versions.

### Summarization Flow

1. The backend loads source text from a stored book or pasted text.
2. The text is chunked when needed.
3. The summarizer sends content to Gemini 2.5 Flash if `GEMINI_API_KEY` is available.
4. If Gemini is unavailable, the system falls back to a local Hugging Face summarizer.
5. The final summary is stored in MongoDB with metadata and progress tracking.

## Installation

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Intelligent_Book_Summarization
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root.

Example:

```env
SECRET_KEY=your_random_secret
JWT_SECRET=your_jwt_secret
MONGODB_URI=mongodb://localhost:27017
DB_NAME=book_summarizer
GEMINI_API_KEY=your_gemini_api_key
HUGGINGFACE_API_KEY=optional_huggingface_key
STREAMLIT_SERVER_PORT=8501
```

## Running the Application

Start the Streamlit app:

```powershell
streamlit run app.py
```

Open the app in your browser at:

```text
http://localhost:8501
```

## Admin Access

Admin access uses the normal login page. The account must exist in MongoDB with `role: "admin"`.

To create an admin user:

```powershell
python backend/create_admin_user.py
```

After login, the admin dashboard becomes available for users with the admin role.

## Testing

### Run the full test suite

```powershell
python run_tests.py
```

### Run individual test groups

```powershell
python -m pytest tests/unit -v
python -m pytest tests/integration -v
python -m pytest tests/security -v
python -m pytest tests/performance -v
```

### Run a single test file

```powershell
python -m pytest tests/integration/test_summarization_flow.py -v
```

## API and Model Notes

- Primary summarization provider: Gemini 2.5 Flash
- Fallback provider: Hugging Face `facebook/bart-base`
- If Gemini requests fail because of network, permissions, or missing API key, the application uses fallback summarization behavior

## Supported Input Formats

- `.txt`
- `.pdf`
- `.docx`

## Export Support

The app supports exporting summaries in:

- TXT
- PDF
- JSON
- clipboard copy flow

## Security Notes

- do not commit `.env`
- do not commit generated test reports or coverage files
- rotate API keys before publishing the repository if they were ever stored locally
- remove hardcoded credentials from utility or test scripts before pushing public code

## Recommended `.gitignore` Entries

```gitignore
.env
.env.*
*.env
.venv/
venv/
__pycache__/
*.pyc
.pytest_cache/
.coverage
logs/
data/
uploads/
temp/
exports/
*_test_results.json
test_report.json
```

## Future Improvements

- stronger role-based admin tooling
- better observability and runtime metrics
- async/background summarization workers
- production-ready deployment config
- improved model routing and caching

## 🚀 Live Demo

👉 https://intelli-book-summarizer-edt8dvhfd8abepywhbgazd.streamlit.app/

## License

Add your preferred license here before publishing.
