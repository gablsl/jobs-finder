import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
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
            
        # Pega as linhas pulando o cabeçalho
        data_rows = all_rows[1:]
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        # Iteramos de trás para frente (do fim para o começo)
        # Isso é crucial porque se deletarmos a linha 2, a linha 3 vira 2, o que bagunçaria o laço comum
        for i in range(len(data_rows) - 1, -1, -1):
            row = data_rows[i]
            if not row or len(row) < 1:
                continue
                
            try:
                # Lê a data que salvamos no Sheets (Ex: "31/05/2026 18:15")
                job_date_str = row[0]
                job_date = datetime.strptime(job_date_str, "%d/%m/%Y %H:%M")
                
                if job_date < cutoff_date:
                    row_number = i + 2 # +1 do cabeçalho e +1 porque o Sheets começa index no 1
                    spreadsheet.delete_rows(row_number)
                    print(f"🗑️ Deleted old job: {row[1]} (Saved on {job_date_str})")
                    deleted_count += 1
            except Exception:
                # Se a linha tiver uma data inválida ou estiver corrompida, pula para não travar
                continue
                
        print(f"✨ Cleanup finished! Total rows removed: {deleted_count}")
    except Exception as e:
        print(f"⚠️ Failed to run database cleanup: {e}")

def send_daily_report():
    """Sua função atual que lê as vagas com status 'Pending', monta o HTML e envia o e-mail"""
    print("📧 Checking for pending jobs to send...")
    
    # ... (Deixe todo o seu código atual de envio aqui) ...
    
    # 🎯 NO FINAL DA FUNÇÃO, onde o e-mail foi enviado com sucesso:
    # Se o e-mail foi enviado (ou se não tinha vaga mas o fluxo rodou), chamamos o gari:
    clean_old_jobs(days_to_keep=7)

if __name__ == "__main__":
    send_daily_report()