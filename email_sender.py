import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import gspread
from main import get_google_sheets_client

def clean_old_jobs(days_to_keep=7):
    """Deletes rows from Google Sheets that are older than X days to keep it clean."""
    print(f"\n🧹 Starting database cleanup (removing jobs older than {days_to_keep} days)...")
    try:
        sheets_client = get_google_sheets_client()
        spreadsheet = sheets_client.open("jobs").sheet1
        
        all_rows = spreadsheet.get_all_values()
        if len(all_rows) <= 1:
            print("💤 Sheet is empty or only has the header. No cleanup needed.")
            return
            
        data_rows = all_rows[1:]
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        # De trás para frente para manter os índices corretos durante a deleção
        for i in range(len(data_rows) - 1, -1, -1):
            row = data_rows[i]
            if not row or len(row) < 1:
                continue
                
            try:
                job_date_str = row[0]
                job_date = datetime.strptime(job_date_str, "%d/%m/%Y %H:%M")
                
                if job_date < cutoff_date:
                    row_number = i + 2  # +1 do cabeçalho, +1 index de tabela (1-based)
                    spreadsheet.delete_rows(row_number)
                    print(f"🗑️ Deleted old job: {row[1]} (Saved on {job_date_str})")
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
        spreadsheet = sheets_client.open("jobs").sheet1
        
        all_rows = spreadsheet.get_all_values()
        if len(all_rows) <= 1:
            print("💤 No jobs found in the spreadsheet.")
            return
            
        header = all_rows[0]
        data_rows = all_rows[1:]
        
        # Filtra apenas linhas com status "Pending"
        pending_jobs = []
        pending_row_indices = [] # Armazena o número real da linha para atualizar o status depois
        
        for idx, row in enumerate(data_rows):
            if len(row) > 5 and row[5] == "Pending":
                pending_jobs.append(row)
                pending_row_indices.append(idx + 2)
                
        if not pending_jobs:
            print("💤 No pending high-score jobs found for today's email.")
            clean_old_jobs(days_to_keep=7)
            return

        print(f"📦 Found {len(pending_jobs)} pending jobs! Building HTML email...")
        
        # Configurações do e-mail
        sender_email = "gablslcontact@gmail.com"
        receiver_email = "gablslcontact@gmail.com"
        password = os.environ.get("GMAIL_APP_PASSWORD")
        
        if not password:
            raise ValueError("⚠️ GMAIL_APP_PASSWORD environment variable not found.")

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🚀 {len(pending_jobs)} Novas Vagas Júnior Filtradas para Você!"
        msg['From'] = sender_email
        msg['To'] = receiver_email

        # Construção das vagas no HTML
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

            # Formata quebras de linha de texto bruto em HTML
            requirements_html = requirements.replace("\n", "<br>")
            experiences_html = experiences.replace("\n", "<br>")

            single_job_html = f"""
            <div style="border: 1px solid #e2e8f0; padding: 24px; border-radius: 12px; margin-bottom: 30px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                <h2 style="color: #1e3a8a; margin-top: 0; font-size: 20px; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px;">
                    {title} <span style="color: #64748b; font-weight: normal; font-size: 16px;">na {company}</span>
                </h2>
                
                <p style="font-size: 15px;"><strong>🎯 Match Score:</strong> <span style="color: #10b981; font-weight: bold;">{score}%</span></p>
                <p><strong>🔗 Link para Aplicar:</strong> <a href="{link}" style="color: #2563eb; font-weight: bold; text-decoration: underline;">Clicar e Aplicar Primeiro</a></p>
                
                <div style="background-color: #f8fafc; border-left: 4px solid #3b82f6; padding: 15px; margin: 15px 0; border-radius: 4px;">
                    <strong style="color: #1e40af; display: block; margin-bottom: 5px;">📋 Requisitos e Foco da Vaga:</strong>
                    <p style="margin: 0; color: #334155; font-size: 14px; line-height: 1.6;">{requirements_html}</p>
                </div>
                
                <p style="margin-top: 15px; margin-bottom: 5px;"><strong>💡 Resumo Adaptado para o ATS:</strong></p>
                <p style="color: #475569; font-size: 14px; line-height: 1.6; background-color: #f9fafb; padding: 12px; border-radius: 6px; border: 1px solid #f1f5f9; margin-top: 0;">{summary}</p>
                
                <p style="margin-top: 15px; margin-bottom: 5px;"><strong>💼 Suas Experiências Adaptadas para Copiar:</strong></p>
                <p style="color: #475569; font-size: 14px; line-height: 1.6; background-color: #f5f3ff; padding: 12px; border-radius: 6px; border: 1px solid #ede9fe; border-left: 4px solid #7c3aed; margin-top: 0;">{experiences_html}</p>
                
                <p style="margin-top: 15px; margin-bottom: 8px;"><strong>🛠️ Palavras-chave de Competências:</strong></p>
                <p style="color: #4b5563; font-size: 13px; margin: 0;">
                    <span style="background-color: #e0e7ff; color: #4338ca; padding: 4px 10px; border-radius: 20px; display: inline-block; margin: 3px 2px;">
                        {skills.replace(", ", "</span> <span style='background-color: #e0e7ff; color: #4338ca; padding: 4px 10px; border-radius: 20px; display: inline-block; margin: 3px 2px;'>")}
                    </span>
                </p>
            </div>
            """
            jobs_html_list.append(single_job_html)

        full_html = f"""
        <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; padding: 20px; margin: 0;">
            <div style="max-width: 650px; margin: 0 auto;">
                <div style="background-color: #1e3a8a; padding: 20px; text-align: center; border-radius: 12px 12px 0 0;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 24px;">Relatório Diário de Oportunidades</h1>
                    <p style="color: #93c5fd; margin: 5px 0 0 0; font-size: 14px;">Seu copiloto de buscas automatizado</p>
                </div>
                <div style="padding: 20px 0;">
                    {"".join(jobs_html_list)}
                </div>
                <div style="text-align: center; color: #94a3b8; font-size: 12px; padding: 20px 0;">
                    <p>Este e-mail foi gerado de forma 100% autônoma pelo seu robô via GitHub Actions.</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(full_html, 'html'))

        # Envia o e-mail via SMTP do Gmail
        print("🚀 Connecting to Gmail SMTP server...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("✨ Email successfully sent to your inbox!")

        # Atualiza o status de "Pending" para "Sent" na planilha
        print("🔄 Updating job statuses in Google Sheets...")
        for row_num in pending_row_indices:
            spreadsheet.update_cell(row_num, 6, "Sent") # Coluna F (6) é o Status
        print("✅ Status updates finished.")

        # Executa a limpeza de dados antigos
        clean_old_jobs(days_to_keep=7)

    except Exception as e:
        print(f"⚠️ Error in email sender module: {e}")

if __name__ == "__main__":
    send_daily_report()