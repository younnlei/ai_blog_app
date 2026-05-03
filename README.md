# Scriptly ✍️

An AI-powered web app that turns YouTube videos into blog posts. 
Paste a link, get an article.



https://github.com/user-attachments/assets/124da642-e75b-4624-ab63-af3e078437ab



## How it works

1. Paste a YouTube link
2. yt-dlp downloads the audio
3. AssemblyAI transcribes it
4. OpenAI GPT-3.5 rewrites it into a clean blog post
5. Post is saved to your personal dashboard

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python, Django |
| Database | SQLite (dev), PostgreSQL (prod) |
| AI | AssemblyAI, OpenAI GPT-3.5 |
| Frontend | HTML, TailwindCSS, JavaScript |
| Hosting | Railway |

## Status

Core pipeline works fully in local development. 
YouTube blocks cloud server IPs in production.

## Run locally

```bash
git clone <your-repo>
cd ai_blog_app
pip3 install -r requirements.txt
export DATABASE_URL=sqlite:///db.sqlite3
python3 manage.py migrate
python3 manage.py runserver
```

Add a `.env` file with:
```
SECRET_KEY=your-secret-key
ASSEMBLYAI_API_KEY=your-key
OPENAI_API_KEY=your-key
FFMPEG_LOCATION=/opt/homebrew/bin
```
