# 🚀 Premium Gatekeeper Portal

A production-ready Telegram Membership Verification Gateway bot built in Python. 

This bot prevents access to your high-value destination links until users join your specified Telegram channels.

---

## 📋 Table of Contents
1. [Prerequisites](#-prerequisites)
2. [Local Testing Setup](#-local-testing-setup)
3. [Required BotFather Settings](#%EF%B8%8F-required-botfather-settings)
4. [Channel & Admin Setup](#-channel--admin-setup)
5. [Configured Campaign Deep Links](#-configured-campaign-deep-links)
6. [Cloud Deployments (Render / Railway)](#-cloud-deployments-render--railway)

---

## 🛠️ Prerequisites
- Python 3.8 or higher.
- A Telegram account and a Telegram Bot token created via [@BotFather](https://t.me/BotFather).
- One or more Telegram Channels (Public or Private) where you want to grow your audience.

---

## 💻 Local Testing Setup

1. **Extract the files** from the downloaded ZIP archive into a dedicated directory.
2. **Open a terminal** in that folder and create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```
3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure your Token**:
   - Rename `.env.example` to `.env`
   - Open `.env` and replace `YOUR_TELEGRAM_BOT_TOKEN_HERE` with your real token from BotFather:
     ```env
     BOT_TOKEN="123456789:ABCDefghIJKL_mnopqrstuvwxyz"
     ```
5. **Start your bot**:
   ```bash
   python bot.py
   ```

---

## ⚙️ Required BotFather Settings
To ensure a high-quality experience, make sure to configure these options inside **@BotFather**:
1. Open [@BotFather](https://t.me/BotFather) and send `/mybots`.
2. Select your bot.
3. Choose **Bot Settings** ➡️ **Group Admin Rights** or **Channel Admin Rights** and ensure the bot has proper administration toggles enabled.
4. Add description and profile pictures for a professional aesthetic!

---

## 📢 Channel & Admin Setup (CRITICAL)
For the bot to verify channel memberships, you **MUST** configure the following:
1. **Add the Bot to the Channel**: Open your Telegram Channel settings, go to **Administrators**, and click **Add Administrator**. Search for your bot username (e.g. `GatewayGatekeeperBot`) and add it.
2. **Assign Required Permissions**: The bot only needs the basic **"Invite Users via Link"** or **"Manage Chat"** permission to query member statuses. It does *not* need posting permissions or administrative control.
3. **Check Username**: Ensure your `config.json` channel usernames match your channel's public usernames (including the `@` prefix).

---

## 🔗 Configured Campaign Deep Links
The following deep links are embedded in this package. Share these links with your users. Once they join your channel, they will automatically unlock the associated destination link:

| Campaign Name | Deep Link Parameter | Channel | Destination | Full t.me Bot Link |
| :--- | :--- | :--- | :--- | :--- |
| **JJK** | `jjk` | `AnimeStreet_backup` | [Link](https://t.me/+3RnRB0avwhk1OTBl) | `https://t.me/GatewayGatekeeperBot?start=jjk` |

---

## ☁️ Cloud Deployments (Render / Railway)

### 📤 1. Push to GitHub
1. Create a new **private** or **public** repository on GitHub.
2. Initialize and push your folder to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initialize gatekeeper bot"
   git branch -M main
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```
   *(Note: Ensure your `.env` file is in `.gitignore` so your actual secret keys are never leaked to GitHub).*

---

### 🚀 2. Deploying to Render (render.com)
Render offers a hassle-free deployment for background processes.
1. Sign up on [Render.com](https://render.com) and link your GitHub account.
2. Click **New** ➡️ Select **Background Worker**.
3. Choose your GitHub repository containing the bot files.
4. Set the following settings:
   - **Language**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
5. Go to **Environment Variables** in the dashboard and add:
   - Key: `BOT_TOKEN` 
   - Value: `your_real_bot_token_from_botfather`
6. Click **Deploy**!

---

### 🚄 3. Deploying to Railway (railway.app)
Railway is another amazing platform to host long-running Python services:
1. Create an account on [Railway.app](https://railway.app).
2. Click **New Project** ➡️ **Deploy from GitHub repo**.
3. Select your bot's repository.
4. Click **Add Variables** and configure:
   - `BOT_TOKEN` = `your_real_bot_token_from_botfather`
5. Railway will automatically detect the Python environment, install `requirements.txt`, and start the bot instantly using `python bot.py`.

---

*Generated with ❤️ by the Telegram Bot & Campaign Generator dashboard.*