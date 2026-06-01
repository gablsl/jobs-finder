# 🚀 Daily Tech Jobs Automation

An autonomous, AI-powered pipeline that scrapes junior tech jobs, evaluates them against your specific profile, and delivers a beautifully tailored daily HTML report straight to your inbox. 

Powered by **GitHub Actions**, this project runs completely in the cloud for free, ensuring you never miss a highly compatible job opening.

---

## 🛠️ Tech Stack

* **Language:** Python 3.11
* **Web Scraping:** Playwright & BeautifulSoup4
* **AI Engine:** Gemini 2.5 Flash (Google GenAI SDK)
* **Database:** Google Sheets API (via gspread)
* **Automation/CI:** GitHub Actions
* **Notification:** SMTP/Gmail API (HTML/CSS Newsletter)

---

## 📋 Features

* **Smart Filtering:** Evaluates jobs using a dynamic JSON profile containing your desired stacks, max experience requirements, and preferred seniority.
* **AI Resume Tailoring:** The Gemini API reads your *actual* past professional experience and dynamically rewrites your resume summary and bullet points to match the specific job description perfectly.
* **Duplicate Prevention:** Uses Google Sheets as a lightweight database to ensure you never process or receive the same job twice.
* **Auto-Cleanup:** Automatically removes spreadsheet entries older than 7 days to keep your ecosystem lean and within free-tier limits.

---

## 🚀 Getting Started: Step-by-Step Setup

### Prerequisites & API Activation

#### Google Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Log in with your Google account and click on **Get API Key**.
3. Create a new key and save it somewhere secure.

#### Google Sheets API (Database Setup)
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Enable the **Google Sheets API** and **Google Drive API** for your project.
4. Go to **Credentials**, click **Create Credentials**, and select **Service Account**.
5. Once created, generate a **JSON Key** for this service account. Download it; this is your `google_credentials.json`.
6. Open your downloaded JSON file, copy the `client_email` address, and **share your Google Sheet** with this email address giving it "Editor" permissions. Ensure your sheet is named `jobs`.

#### Gmail App Password (SMTP)
1. Go to your Google Account Security settings.
2. Enable **2-Step Verification**.
3. Search for **App Passwords**.
4. Create a new App Password (e.g., name it "Job Robot") and copy the 16-character code generated.

---

### Local Development & Testing

#### Clone the Project
```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git)
cd YOUR_REPOSITORY_NAME
```

#### Install dependêncies
```bash
pip install -r requirements.txt
playwright install chromium
```

#### Configure your profile

Create a config.json file in the root directory. This holds your profile and past experiences that the AI will use to match and rewrite:

```bash
{
  "candidate_name": "Your Name",
  "seniority_focus": "Junior",
  "max_years_experience": 3,
  "desired_stacks": ["Node.js", "TypeScript", "Python"],
  "min_match_score": 65,
  "past_experiences": [
    {
      "company": "Company A",
      "role": "Junior Developer",
      "duration_months": 12,
      "technologies": ["Node.js", "MySQL"],
      "description": [
        "Developed web applications using Node.js.",
        "Participated in API integrations."
      ]
    }
  ]
}
```

#### Run locally

Set up your local environment variables and execute the pipeline:

```bash
export GEMINI_API_KEY="your_api_key"
export SENDER_EMAIL="your_email@gmail.com"
export RECEIVER_EMAIL="your_email@gmail.com"
export GMAIL_APP_PASSWORD="your_app_password"
export SPREADSHEET_NAME="your_spreadsheet_name"

python scraper.py
python email_sender.py
```

### Deploying to GitHub Actions (Cloud Automation)

To make this pipeline run completely automatically every day, you need to add your credentials as **Secrets** in your GitHub repository.

1. On GitHub, navigate to your repository.
2. Go to **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret** and add the following 6 secrets:

| Secret Name | Value Description |
| :--- | :--- |
| `GEMINI_API_KEY` | Your Google AI Studio API key |
| `GMAIL_APP_PASSWORD` | The 16-character Gmail app password |
| `SENDER_EMAIL` | The email address sending the report |
| `RECEIVER_EMAIL` | The email address receiving the report |
| `GOOGLE_CREDENTIALS_JSON` | The entire content of your `google_credentials.json` file |
| `USER_CONFIG_JSON` | The entire content of your `config.json` profile file |
| `SPREADSHEET_NAME` | The name of sheet in Google Sheet |

---

## ⏰ Schedule Execution

The automation is configured via GitHub Actions (`.github/workflows/main.yml`) to run **every day at 09:00 AM Brasília Time (12:00 PM UTC)**. 

You can also trigger it manually at any time by going to the **Actions** tab on your GitHub repository website, selecting the workflow, and clicking **Run workflow**.

---

## 📄 License
This project is open-source and available under the MIT License. Feel free to fork, customize, and share!
