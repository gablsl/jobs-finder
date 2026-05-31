import os
import json
from datetime import datetime
import traceback
import gspread
from google.oauth2.service_account import Credentials
from google import genai
from google.genai import types

def get_google_sheets_client():
    """Authenticates with Google API using the JSON string from environment variables or local file."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    json_env = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    
    if json_env:
        info = json.loads(json_env)
        credentials = Credentials.from_service_account_info(info, scopes=scopes)
    else:
        credentials_path = "google_credentials.json"
        credentials = Credentials.from_service_account_file(credentials_path, scopes=scopes)
        
    return gspread.authorize(credentials)

def analyze_job_position(title: str, description: str) -> dict:
    """Analyzes the job description against Gabriel's profile using Gemini 2.5 Flash."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("⚠️ GEMINI_API_KEY environment variable not found.")
        
    gemini_client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Você é um especialista em recrutamento técnico e ATS. Analise a vaga abaixo e compare com o perfil do Gabriel (Desenvolvedor Fullstack Node/TS/Python).
    
    Vaga: {title}
    Descrição Bruta: {description}

    Gere uma resposta estritamente em formato JSON com os seguintes campos:
    - is_valid_match (boolean): true se for uma vaga Júnior relevante para o perfil do Gabriel.
    - score (int): nota de compatibilidade de 0 a 100.
    - adapted_summary (string): O resumo profissional do Gabriel adaptado para esta vaga.
    - adapted_skills (string): As palavras-chave de tecnologia separadas por vírgula para passar no ATS.
    - job_requirements (string): Um resumo curto e direto (em até 4 tópicos com bullet points) dos requisitos técnicos reais exigidos pela vaga.
    - tailored_experiences (string): Gere de 3 a 4 bullet points profissionais prontos, simulando as experiências anteriores do Gabriel, mas usando os termos e conquistas que dão mais match com os requisitos dessa vaga específica.
    """

    # Definindo o esquema de validação estrito para o Gemini não errar o JSON
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "is_valid_match": {"type": "BOOLEAN"},
            "score": {"type": "INTEGER"},
            "adapted_summary": {"type": "STRING"},
            "adapted_skills": {"type": "STRING"},
            "job_requirements": {"type": "STRING"},
            "tailored_experiences": {"type": "STRING"}
        },
        "required": ["is_valid_match", "score", "adapted_summary", "adapted_skills", "job_requirements", "tailored_experiences"]
    }

    response = gemini_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=0.3
        ),
    )
    
    return json.loads(response.text)

def process_and_save_job(title: str, company: str, link: str, description: str):
    """Analyzes the job and saves the data into Google Sheets if it's a good match."""
    try:
        analysis = analyze_job_position(title, description)
        
        if not analysis.get("is_valid_match") or analysis.get("score", 0) < 70:
            print(f"❌ Job skipped (Low match score or wrong seniority). Score: {analysis.get('score')}%")
            return

        print(f"🎯 Great match found! Score: {analysis.get('score')}%. Connecting to Google Sheets...")
        
        sheets_client = get_google_sheets_client()
        spreadsheet = sheets_client.open("jobs").sheet1
        
        current_date = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # Mapeamento exato batendo com as colunas A até J da sua planilha
        row_data = [
            current_date,                         # A: Date
            title,                                # B: Title
            company,                              # C: Company
            link,                                 # D: Link
            int(analysis.get("score")),           # E: Score
            "Pending",                            # F: Status
            analysis.get("adapted_summary"),      # G: Adapted_Summary
            analysis.get("adapted_skills"),       # H: Adapted_Skills
            analysis.get("job_requirements"),     # I: Job_Requirements (Nova)
            analysis.get("tailored_experiences")  # J: Tailored_Experiences (Nova)
        ]
        
        spreadsheet.append_row(row_data, value_input_option="USER_ENTERED")
        print("💾 Data successfully saved to Google Sheets!")
        
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print("⏳ [Rate Limit] Gemini API free tier limit reached. Skipping position to avoid crash...")
        else:
            print(f"⚠️ An error occurred while processing the job: {e}")
            traceback.print_exc()