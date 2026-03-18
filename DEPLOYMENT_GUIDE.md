# Level 3: Official Cloud Deployment Architecture

If you want to absolutely stun your academic defense panel, you should not run this project on `localhost`. Running a localized prototype proves you can script; running a globally accessible architecture proves you are an enterprise Software Engineer.

Because we successfully decoupled your SQL database by piping all data to the **Supabase PostgreSQL Cloud**, your Streamlit frontend is entirely stateless. This means deploying it to the internet is a trivial 60-second process.

## Option A: Streamlit Community Cloud (Recommended & Free)
Streamlit Cloud is natively integrated with GitHub and automatically handles the `requirements.txt` containerization for you.

1. Create a free account at [share.streamlit.io](https://share.streamlit.io/).
2. Click **New App** and authorize your GitHub repository.
3. Select your repository: `AI-driven-Autonomous-SOC`.
4. Set the Main file path to: `dashboard.py`.
5. **CRITICAL STEP:** Before clicking Deploy, click on **Advanced Settings**. You must inject your Supabase environment variables here so the cloud server can reach your database. In the Secrets box, paste:
   ```toml
   SUPABASE_URL="your-supabase-url-here"
   SUPABASE_SERVICE_KEY="your-supabase-service-key-here"
   GROQ_API_KEY="your-groq-key-here"
   ABUSEIPDB_API_KEY="your-abuseipdb-here"
   ```
6. Click **Deploy**. Within 3 minutes, your terminal will spin up, and you'll be handed a public URL (e.g., `https://autonomous-soc-cortex.streamlit.app`) to share with your professors!

## Option B: Render.com (Docker Deployment)
If you want to prove your Docker orchestration skills, Render natively parses the `Dockerfile` we built earlier.

1. Create an account at [Render.com](https://render.com/).
2. Select **New Web Service** -> Build and Deploy from a Git Repository.
3. Connect your GitHub Repo.
4. Render will automatically detect the `Dockerfile` as the deployment method.
5. In the **Environment Variables** section, paste the exact same `.env` keys listed above.
6. Click **Deploy**. Your autonomous matrix is now running in an isolated Linux container on the internet.

### Pre-Presentation Advice: The Hollywood Simulator
Right before you plug your laptop into the projector for your defense:
1. Open up your local terminal.
2. Run exactly: `python hollywood_simulator.py`
3. This will silently fire 250 highly-malicious, global cyber-attacks into your Supabase database.
4. When you open your public Cloud URL, the dashboard's Plotly globe will physically light up with massive red alert vectors across Russia, China, and North Korea, making the system look incredibly active and battle-tested for the panel!
