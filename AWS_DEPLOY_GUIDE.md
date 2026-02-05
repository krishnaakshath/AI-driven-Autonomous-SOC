# AWS Deployment Guide ☁️

To deploy your SOC to AWS so it runs 24/7 (even when your laptop is closed), follow these steps.

## Prerequisites
1.  **AWS Account** (Free Tier is fine).
2.  **Gmail App Password** (for alerts).

## Step 1: Launch AWS Instance
1.  Go to **AWS Console** > **EC2**.
2.  Click **Launch Instance**.
3.  Name: `SOC-Server`.
4.  OS Image: **Ubuntu Server 24.04 LTS**.
5.  Instance Type: **t3.medium** (t2.micro might run out of RAM for ML).
6.  Key Pair: Create a new one, download the `.pem` file.
7.  **Network Settings**: Check boxes for "Allow HTTP" and "Allow HTTPS".

## Step 2: Connect to Server
Open your terminal (on Mac) and run:
```bash
chmod 400 your-key.pem
ssh -i "your-key.pem" ubuntu@<YOUR-EC2-PUBLIC-IP>
```

## Step 3: Install Docker & Deploy
Run these commands inside the EC2 server:

```bash
# 1. Update & Install Docker
sudo apt update && sudo apt install -y docker.io docker-compose

# 2. Clone Your Repo
git clone https://github.com/KrishnaAkshath/AI-driven-Autonomous-SOC.git
cd AI-driven-Autonomous-SOC

# 3. Configure Secrets (Environment Variables)
nano .env
```
*Paste the following into the `.env` file:*
```ini
GROQ_API_KEY=your_key_here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password_here
```
*(Press Ctrl+X, then Y, then Enter to save)*

# 4. Launch 🚀
sudo docker-compose up -d --build
```

## Step 4: Access Your SOC
Visit `http://<YOUR-EC2-PUBLIC-IP>:8501` in your browser.

✅ **Status:**
- **Website:** Running on port 8501.
- **Background Monitor:** Running silently, checking threats every 60s.
- **Alerts:** Will email you automatically if a Critical Threat is found.
