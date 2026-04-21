# Cyber Command Dashboard - Deployment Guide

This project is optimized for both desktop and mobile devices. Follow the steps below to get your **permanent public link**.

## Prerequisites
1. A [GitHub](https://github.com/) account.
2. A [Render](https://render.com/) account (Free).

## Step 1: Push to GitHub
1. Create a new repository on GitHub named `cyber-command`.
2. Open your terminal in this folder and run:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/cyber-command.git
   git push -u origin main
   ```

## Step 2: Deploy to Render
1. Go to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** > **Web Service**.
3. Connect your GitHub account and select the `cyber-command` repository.
4. Use these settings:
   - **Name:** `cyber-command`
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn server:app`
5. Click **Create Web Service**.

Render will give you a link like `https://cyber-command.onrender.com`. This is your **permanent link**.

## Step 3: Persistence (SQLite)
> [!NOTE]
> On Render's free tier, the database (`security_system.db`) resets every time the server restarts. For a truly permanent database, consider upgrading to a "Blueprint" with a persistent disk or switching to a PostgreSQL database.

## Support
If you have any issues with alignment or the link, ask Antigravity!
