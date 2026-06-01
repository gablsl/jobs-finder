import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from main import get_google_sheets_client

def clean_old_jobs(days_to_keep=7):
    """Deletes rows from Google Sheets that are older than X days to keep it clean."""
    print(f"\n🧹 Starting database cleanup (removing jobs older than {days_to_keep} days)...")
    try:
        sheets_client = get_google_sheets_client()
        sheet_name = os.environ.get("SPREADSHEET_NAME")
        spreadsheet = sheets_client.open(sheet_name).sheet1
        all_rows = spreadsheet.get_all_values()
        if len(all_rows) <= 1:
            return
            
        data_rows = all_rows[1:]
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        for i in range(len(data_rows) - 1, -1, -1):
            row = data_rows[i]
            if not row or len(row) < 1:
                continue
            try:
                job_date_str = row[0]
                job_date = datetime.strptime(job_date_str, "%d/%m/%Y %H:%M")
                if job_date < cutoff_date:
                    spreadsheet.delete_rows(i + 2)
                    deleted_count += 1
            except Exception:
                continue
        print(f"✨ Cleanup finished! Total rows removed: {deleted_count}")
    except Exception as e:
        print(f"⚠️ Failed to run database cleanup: {e}")

def send_daily_report():
    """Fetches 'Pending' jobs from Google Sheets, structures a premium HTML email and sends it."""
    print("📧 Connecting to Google Sheets to check for pending report jobs...")
    try:
        sheets_client = get_google_sheets_client()
        sheet_name = os.environ.get("SPREADSHEET_NAME")
        spreadsheet = sheets_client.open(sheet_name).sheet1
        all_rows = spreadsheet.get_all_values()
        if len(all_rows) <= 1:
            print("💤 No jobs found in the spreadsheet.")
            return
            
        data_rows = all_rows[1:]
        pending_jobs = []
        pending_row_indices = []
        
        for idx, row in enumerate(data_rows):
            if len(row) > 5 and row[5] == "Pending":
                pending_jobs.append(row)
                pending_row_indices.append(idx + 2)
                
        if not pending_jobs:
            print("💤 No pending high-score jobs found for today's email.")
            clean_old_jobs(days_to_keep=7)
            return

        print(f"📦 Found {len(pending_jobs)} pending jobs! Building HTML email...")
        
        # Fetch email configurations dynamically from environment variables
        sender_email = os.environ.get("SENDER_EMAIL")
        receiver_email = os.environ.get("RECEIVER_EMAIL")
        password = os.environ.get("GMAIL_APP_PASSWORD")
        
        if not sender_email or not receiver_email or not password:
            raise ValueError(
                "⚠️ Missing email configuration. Please ensure SENDER_EMAIL, "
                "RECEIVER_EMAIL, and GMAIL_APP_PASSWORD are set in the environment."
            )

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🚀 {len(pending_jobs)} Novas Vagas Júnior (Multi-stack) Encontradas!"
        msg['From'] = sender_email
        msg['To'] = receiver_email

        jobs_html_list = []
        for row in pending_jobs:
            title = row[1]
            company = row[2]
            link = row[3]
            score = row[4]
            summary = row[6] if len(row) > 6 else ""
            skills = row[7] if len(row) > 7 else ""
            requirements = row[8] if len(row) > 8 else "Não informado"
            experiences = row[9] if len(row) > 9 else "Não informado"

            # Security formatting for line breaks in HTML
            requirements_html = requirements.replace("\n", "<br>")
            experiences_html = experiences.replace("\n", "<br>")

            skills_list = [s.strip() for s in skills.split(",") if s.strip()]
            skills_html = "".join([f"<span style='background-color: #e0e7ff; color: #4338ca; padding: 4px 10px; border-radius: 20px; display: inline-block; margin: 3px 2px; font-size: 12px;'>{skill}</span>" for skill in skills_list])

            single_job_html = f"""
            <div style="border: 1px solid #e2e8f0; padding: 24px; border-radius: 12px; margin-bottom: 30px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                <h2 style="color: #1e3a8a; margin-top: 0; font-size: 20px; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px;">
                    {title} <span style="color: #64748b; font-weight: normal; font-size: 16px;">na {company}</span>
                </h2>
                
                <p style="font-size: 15px; margin: 8px 0;"><strong>🎯 Score de Compatibilidade:</strong> <span style="color: #10b981; font-weight: bold;">{score}%</span></p>
                <p style="font-size: 15px; margin: 8px 0;"><strong>🔗 Link Direto:</strong> <a href="{link}" style="color: #2563eb; font-weight: bold; text-decoration: underline;">Clique aqui para se candidatar</a></p>
                
                <div style="background-color: #f8fafc; border-left: 4px solid #0284c7; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <strong style="color: #0369a1; display: block; margin-bottom: 8px; font-size: 15px;">📋 Descrição Completa e Requisitos da Vaga:</strong>
                    <div style="margin: 0; color: #334155; font-size: 14px; line-height: 1.6;">{requirements_html}</div>
                </div>
                
                <p style="margin-top: 15px; margin-bottom: 5px;"><strong>💡 Resumo Adaptado para o ATS:</strong></p>
                <p style="color: #475569; font-size: 14px; line-height: 1.6; background-color: #f9fafb; padding: 12px; border-radius: 6px; border: 1px solid #f1f5f9; margin-top: 0;">{summary}</p>
                
                <p style="margin-top: 15px; margin-bottom: 5px;"><strong>💼 Suas Experiências Adaptadas para Copiar:</strong></p>
                <p style="color: #475569; font-size: 14px; line-height: 1.6; background-color: #f5f3ff; padding: 12px; border-radius: 6px; border: 1px solid #ede9fe; border-left: 4px solid #7c3aed; margin-top: 0;">{experiences_html}</p>
                
                <p style="margin-top: 15px; margin-bottom: 8px;"><strong>🛠️ Stack Tecnológica Envolvida:</strong></p>
                <div style="margin: 0;">{skills_html}</div>
            </div>
            """
            jobs_html_list.append(single_job_html)

        full_html = f"""
        <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; padding: 20px; margin: 0;">
            <div style="max-width: 650px; margin: 0 auto;">
                <div style="background-color: #1e3a8a; padding: 20px; text-align: center; border-radius: 12px 12px 0 0;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 24px;">Relatório de Vagas Júnior Multi-Stack</h1>
                    <p style="color: #93c5fd; margin: 5px 0 0 0; font-size: 14px;">Análise preditiva de mercado</p>
                </div>
                <div style="padding: 20px 0;">
                    {"".join(jobs_html_list)}
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(full_html, 'html'))

        print("🚀 Connecting to Gmail SMTP server...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("✨ Email successfully sent to your inbox!")

        print("🔄 Updating job statuses in Google Sheets...")
        for row_num in pending_row_indices:
            spreadsheet.update_cell(row_num, 6, "Sent")
        print("✅ Status updates finished.")
        clean_old_jobs(days_to_keep=7)

    except Exception as e:
        print(f"⚠️ Error in email sender module: {e}")

if __name__ == "__main__":
    send_daily_report()