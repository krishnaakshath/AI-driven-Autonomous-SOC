# 🚀 How to Deploy Your AI-SOC Dashboard

Since I cannot click buttons on websites for you, here is the exact guide to **deploy your actual Python application** (the one with the new Cyberpunk theme) to the cloud.

I have prepared all the configuration files. You just need to push the code and connect it.

---

## Option 1: Streamlit Cloud (Easiest)
**Best for:** Free, fast, designed for Streamlit apps.

1. **Push to GitHub**
   - Open your terminal and run:
     ```bash
     git add .
     git commit -m "Update SOC with Cyberpunk Theme"
     git push
     ```

2. **Deploy**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Login with GitHub.
   - Click **"New app"**.
   - Select your repository: `KrishnaAkshath/AI-driven-Autonomous-SOC` (or strictly the one you are working on).
   - **Main file path:** `streamlit_app.py`
   - Click **Deploy!**

It will detect `requirements.txt` automatically and install everything.

---

## Option 2: Render.com
**Best for:** Professional hosting, supports generic Python apps.

1. **Push to GitHub** (same as above).

2. **Deploy on Render**
   - Go to [render.com](https://render.com)
   - Click **New +** -> **Web Service**.
   - Connect your GitHub repo.
   - It should auto-detect the configuration because I created a `render.yaml` file for you.
   - If not, use:
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0`
   - Click **Create Web Service**.

---

## 🛠️ What I Did based on your request
1. **Frontend Update:** I copied the new Cyberpunk dashboard to `pages/1_Dashboard.py` so it appears correctly in the app navigation.
2. **Landing Page:** I updated `streamlit_app.py` to use the same particles/neon theme.
3. **Config Check:** Verified `requirements.txt` and `render.yaml` are ready.

**The "Vercel v0" Prompt:**
If you still want the React version from Vercel v0 (which is just a UI mock, not the real app), refer to the `V0_INSTRUCTIONS.md` file I created earlier.
