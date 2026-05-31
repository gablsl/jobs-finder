# 🚀 Autonomous AI Tech Jobs Finder & Resume Tailor

An autonomous, zero-cost pipeline that scrapes junior tech job opportunities, filters them using the Gemini AI API based on a developer profile, saves structured metrics into Google Sheets, and sends a daily customized HTML digest email. 

Additionally, the system acts as an AI resume builder—generating custom ATS-optimized professional summaries, matching keywords, and tailored experience bullet points for every single high-score job found.

---

## 🏗️ Architecture & Workflow

1. **Scrape (`Playwright` + `BeautifulSoup`)**: Automatically wakes up every morning to fetch freshly posted junior positions from tech boards (e.g., Remotar). It cross-references with Google Sheets to skip previously processed links, saving precious API credits.
2. **Analyze (`Gemini 2.5 Flash`)**: Processes the job description against the candidate's profile. It determines a match score (0-100%). If it's a solid match (Score >= 70%), it automatically generates tailored resume sections.
3. **Database (`Google Sheets API`)**: Appends the structured job data and the AI-generated tailored content into a Google spreadsheet acting as a lightweight cloud database.
4. **Notify (`SMTPLib` / Gmail)**: Gathers all daily pending positions into a premium-designed, responsive HTML email report sent directly to your inbox.
5. **Database Janitor (`gspread`)**: Automatically maintains sheet health by purging tracked opportunities older than 7 days.
6. **Automation (`GitHub Actions`)**: Built entirely on top of a serverless, free-tier CI/CD workflow running completely autonomously in the cloud via cron schedules.

---

## 🛠️ Tech Stack

* **Language:** Python 3.11
* **Web Scraping:** Playwright (Headless Chromium), BeautifulSoup4
* **Artificial Intelligence:** Google Gemini 2.5 Flash API (`google-genai`)
* **Cloud Database:** Google Sheets API (`gspread`, `google-auth`)
* **Automation / CI-CD:** GitHub Actions (Linux Ubuntu Runner)
* **Notifications:** SMTP SSL (Gmail App Passwords)

---

## 📊 Google Sheets Schema

The spreadsheet acts as our relational store. Ensure your primary sheet is named `jobs` and contains the following header row from column **A** to **J**:

| Col | Field Name | Description |
| :--- | :--- | :--- |
| **A** | `Date` | Timestamp of the scraping extraction. |
| **B** | `Title` | The scraped job position title. |
| **C** | `Company` | Extracted or inferred hiring company name. |
| **D** | `Link` | Absolute URL to the job application page (Unique Key). |
| **E** | `Score` | Gemini AI-calculated candidate match percentage (0-100). |
| **F** | `Status` | Processing pipeline lifecycle flag (`Pending` / `Sent`). |
| **G** | `Adapted_Summary` | Customized professional summary targeting the job's core scope. |
| **H** | `Adapted_Skills` | ATS-ready tech stack keywords separated by commas. |
| **I** | `Job_Requirements` | Compact, 3-to-4 bullet points outlining key job expectations. |
| **J** | `Tailored_Experiences` | Contextual bullet points rewritten to mirror job goals for your CV. |

---

## ⚙️ Setup & Installation

### 1. Local Development
Clone the repository and install the dependencies within a virtual environment:

```bash
# Clone the repository
git clone [https://github.com/gablsl/jobs-finder.git](https://github.com/gablsl/jobs-finder.git)
cd jobs-finder

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install requests beautifulsoup4 gspread google-auth google-genai playwright
playwright install chromium

### Configure Repository Secrets & Environment Variables

Before running the pipeline, you must inject the required credentials into your GitHub repository. Navigate to your GitHub Repository **Settings -> Secrets and variables -> Actions**, click on **New repository secret**, and add the following keys:

| Secret Key | Required By | Description |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | `main.py` | Your Google Gemini Developer API token. Used by the AI model to analyze descriptions and tailor your resume data. |
| `GOOGLE_CREDENTIALS_JSON` | `scraper.py` & `email_sender.py` | The entire raw text string from your downloaded Google Cloud Service Account `json` key file. Allows the scripts to read/write columns and perform database cleanups. |
| `GMAIL_APP_PASSWORD` | `email_sender.py` | A unique 16-character security password generated under your Google Account Settings (Security -> 2-Step Verification -> App Passwords). **Must be pasted without any spaces**. |

### Workflow Trigger

The workflow engine is defined at `.github/workflows/daily_robot.yml`. It is programmed to automatically wake up everyday at **09:00 UTC (06:00 AM Brasília Time)**.

* **Automated Schedule:** Runs via a GitHub native `cron` trigger.
* **Manual Trigger:** You can manually dispatch the execution at any moment by navigating to the **Actions** tab on your GitHub repository, selecting **Daily Tech Jobs Automation**, and clicking the **Run workflow** dropdown button.
