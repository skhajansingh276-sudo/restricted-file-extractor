# 🌍 DrivePDF Master: Deployment Guide

This guide explains how to host your backend online so your Android app works for anyone, anywhere in the world.

---

## Step 1: Get Your Browserless Token (Free)
1. Go to [Browserless.io](https://www.browserless.io/).
2. Sign up for a free account.
3. Copy your **API Token** from the dashboard.

## Step 2: Upload Code to GitHub
1. Create a **New Repository** on [GitHub](https://github.com/new).
2. Upload the following files/folders from your project:
   - `app.py`
   - `requirements.txt`
   - `templates/` (folder)
   - `Dockerfile`
   - `android_app/` (folder)

---

## Step 3: Host on Render.com
1. Create an account on [Render.com](https://render.com/).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository.
4. Use these settings:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Click **Advanced** -> **Add Environment Variable**:
   - Key: `BROWSERLESS_KEY`
   - Value: `(Paste your token from Step 1)`
6. Click **Create Web Service**.

---

## Step 4: Update Your Android App
1. Once Render finishes, you will get a link like: `https://drive-pdf.onrender.com`.
2. Open your Android App on your phone.
3. Click the **Settings (Gear Icon)** in the top right.
4. Paste your Render link and click **Save**.

**Congratulations! Your app is now global!**
