import os
import smtplib
import json
import gspread
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2.service_account import Credentials

# =====================================================================
# CONFIGURATION
# =====================================================================
SENDER_EMAIL = "gablslcontact@gmail.com"
# Store your 16-digit app password in your terminal env variables
SENDER_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD") 
RECEIVER_EMAIL = "gablslcontact@gmail.com"

def get_google_sheets_client():
    """Authenticates with Google API using the JSON string from environment variables or local file."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # 1. Check if running on GitHub Actions (via env variable)
    json_env = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    
    if json_env:
        # Load credentials directly from the environment string
        info = json.loads(json_env)
        credentials = Credentials.from_service_account_info(info, scopes=scopes)
    else:
        # Fallback to local file for development
        credentials_path = "google_credentials.json"
        credentials = Credentials.from_service_account_file(credentials_path, scopes=scopes)
        
    return gspread.authorize(credentials)

def send_daily_jobs_email():
    """Reads pending high-score jobs from Google Sheets and sends an HTML email report."""
    try:
        # 1. Connect to Google Sheets
        sheets_client = get_google_sheets_client()
        spreadsheet = sheets_client.open("jobs").sheet1 # Using your sheet name 'jobs'
        
        # 2. Fetch all rows (returns list of dicts based on headers)
        all_records = spreadsheet.get_all_records()
        
        pending_jobs = []
        rows_to_update = [] # Keep track of which row index needs status change
        
        # Google Sheets rows are 1-indexed, and header is row 1, so data starts at row 2
        for index, record in enumerate(all_records, start=2):
            # Filter criteria: Status is Pending and Score is high enough
            if record.get("Status") == "Pending" and int(record.get("Score", 0)) >= 75:
                # Store row index along with job data
                pending_jobs.append(record)
                rows_to_update.append(index)
                
        if not pending_jobs:
            print("💤 No pending high-score jobs found for today's email.")
            return

        print(f"📦 Found {len(pending_jobs)} pending jobs. Building HTML email...")

        # 3. Construct the HTML email body
        email_html = """
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <h2 style="color: #1a73e8;">🚀 Vagas do Dia Adaptadas para o Gabriel</h2>
            <p>Aqui estão as melhores oportunidades Júnior encontradas hoje com o currículo sob medida:</p>
            <hr style="border: 0; border-top: 1px solid #eee;" />
        """
        
        for job in pending_jobs:
            email_html += f"""
            <div style="margin-bottom: 30px; padding: 15px; border-left: 4px solid #1a73e8; background-color: #f8f9fa;">
                <h3 style="margin-top: 0; color: #111;">{job.get('Title')} - <span style="color: #555;">{job.get('Company')}</span></h3>
                <p>🎯 <strong>Match Score:</strong> <span style="color: #1e7e34; font-size: 1.1em;">{job.get('Score')}%</span></p>
                <p>🔗 <strong>Link para Aplicar:</strong> <a href="{job.get('Link')}" style="color: #1a73e8; text-decoration: none; font-weight: bold;">[👉 Clicar e Aplicar Primeiro]</a></p>
                
                <h4 style="margin-bottom: 5px; color: #333;">📝 Resumo Adaptado para o ATS:</h4>
                <p style="font-style: italic; background: #fff; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">{job.get('Adapted_Summary')}</p>
                
                <h4 style="margin-bottom: 5px; color: #333;">🛠️ Habilidades em Destaque:</h4>
                <p style="background: #fff; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">{job.get('Adapted_Skills')}</p>
            </div>
            """
            
        email_html += """
            <p style="font-size: 0.8em; color: #777; margin-top: 4px;">Robô de Vagas v1.0 - Rodando 100% automático no GitHub Actions.</p>
        </body>
        </html>
        """

        # 4. Setup SMTP Connection and Send Email via Gmail
        print("🔌 Connecting to Gmail SMTP server...")
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚀 VAGAS DO DIA - {len(pending_jobs)} Novas Oportunidades Júnior"
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg.attach(MIMEText(email_html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
            
        print("✉️ Email successfully sent!")

        # 5. Update Status in Google Sheets from 'Pending' to 'Sent'
        print("🔄 Updating job statuses in Google Sheets...")
        for row_index in rows_to_update:
            # Column 6 is the 'Status' column (F)
            spreadsheet.update_cell(row_index, 6, "Sent")
            
        print("✅ Sheet updated successfully. Flow complete!")

    except Exception as e:
        print(f"⚠️ Error in email sender module: {e}")

if __name__ == "__main__":
    send_daily_jobs_email()