# 🤖 AI Data Insights Tool

A full-stack web application that lets users upload any CSV dataset, get instant automated analysis with charts, and ask questions about their data in plain English using AI.

## Features

- **User Authentication** — secure signup, login and logout with hashed passwords
- **CSV Upload & Auto Analysis** — upload any CSV and instantly get summary stats, charts and correlations
- **AI Chat** — ask questions about your data in plain English, powered by Groq (LLaMA 3)
- **Auto Charts** — bar charts, histograms and grouped charts generated automatically
- **Summary Statistics** — mean, min, max, std, count for every numeric column
- **Analysis History** — every upload is saved and accessible per user
- **Personal Dashboard** — each user sees only their own data and history

## Tech Stack

- **Backend** — Python, Flask
- **Database** — SQLite
- **Auth** — Werkzeug password hashing, Flask sessions
- **Data Analysis** — Pandas
- **Charts** — Matplotlib
- **AI** — Groq API (LLaMA 3.1)
- **Frontend** — HTML, CSS, JavaScript

## How to Run

1. Clone the repo
   ```
   git clone https://github.com/anagha656/ai-data-insights.git
   cd ai-data-insights
   ```

2. Install dependencies
   ```
   pip install flask flask-cors werkzeug groq python-dotenv matplotlib pandas
   ```

3. Create a `.env` file and add your Groq API key
   ```
   GROQ_API_KEY=your_groq_key_here
   ```
   Get a free key at console.groq.com

4. Start the server
   ```
   python app.py
   ```

5. Open your browser
   ```
   http://127.0.0.1:5000
   ```

## How to Use

1. Create an account on the signup page
2. Login with your credentials
3. Upload any CSV file on the dashboard
4. View auto-generated charts and summary statistics
5. Ask the AI questions about your data in plain English
6. View your analysis history below the dashboard

## Project Structure

```
ai-data-insights/
├── app.py          # Flask backend — auth, analysis, AI chat
├── index.html      # Login and signup page
├── dashboard.html  # Main dashboard — upload, charts, AI chat
├── .env            # API keys (not uploaded to GitHub)
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | Login/signup page |
| GET | /dashboard | User dashboard (login required) |
| POST | /signup | Create a new account |
| POST | /login | Login to existing account |
| POST | /logout | Logout current user |
| GET | /me | Get current logged in user |
| POST | /upload | Upload and analyze a CSV file |
| POST | /ask | Ask AI a question about uploaded data |
| GET | /history | Get user's analysis history |

## What I Learned

- User authentication — password hashing, sessions, protected routes
- Building a multi-user Flask application with SQLite
- Advanced Pandas — describe, isnull, dtypes, groupby, corr
- Auto-generating charts with Matplotlib based on column types
- Integrating Groq AI API to answer questions about data
- Connecting frontend to backend with fetch() and credentials

## Author

Anagha — B.Tech Computer Science, 4th Semester
