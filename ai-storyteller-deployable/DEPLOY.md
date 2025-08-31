# Deployment instructions

## Deploy to Streamlit Cloud (recommended, easiest)
1. Push this repo to GitHub (create a new repo, commit & push).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click "New app" → choose repo, branch (main), and the path to `app.py`.
4. Add any environment variables (e.g., OPENAI_API_KEY) in the app settings.
5. Click "Deploy".

## Deploy to Heroku / Render
- Heroku: Create app, set buildpack to python, set `OPENAI_API_KEY` in config vars, push repo.
- Render: Connect GitHub repo, use the example `render.yaml` above or configure manually.