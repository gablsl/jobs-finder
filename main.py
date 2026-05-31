import os
import json
import traceback
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from google import genai
from google.genai import types

# =====================================================================
# CONFIGURATION & INITIALIZATION
# =====================================================================

# Initialize the Gemini Client
gemini_client = genai.Client()

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

# =====================================================================
# CORE LOGIC FUNCTIONS
# =====================================================================

def analyze_job_position(title: str, description: str) -> dict:
    """Sends job details to Gemini API and returns a structured match analysis."""
    
    prompt = f"""
    Você é um recrutador técnico especialista em sistemas de triagem de currículos (ATS).
    Avalie a vaga abaixo em relação ao currículo do candidato Gabriel Leitão.
    
    FOCO DO CANDIDATO: Vagas de nível JÚNIOR.
    
    VAGA ENCONTRADA:
    Título: {title}
    Descrição: {description}
    
    INSTRUÇÕES CRÍTICAS:
    1. Se a vaga exigir senioridade avançada (Pleno, Sênior, Specialist, Lead) ou mais de 4-5 anos de experiência obrigatória, a nota deve ser baixa e o campo 'is_valid_match' deve ser obrigatoriamente FALSE. Foque estritamente em vagas compatíveis com nível Júnior.
    2. Calcule uma nota de match de 0 a 100 baseada puramente nos requisitos técnicos da vaga e na experiência de 3 anos do Gabriel.
    3. Se a nota for maior ou igual a 75 (e for uma vaga adequada para nível júnior), reescreva o "Resumo Profissional" e reordene as "Habilidades Técnicas" do Gabriel para dar ênfase máxima ao que a vaga pede (seja Java, Python, Node, Next.js, etc).
    4. Mantenha os textos gerados (justificativa, resumo e skills) em PORTUGUÊS.
    5. NÃO invente mentiras ou experiências que ele não tem. Apenas mude a ênfase para destacar as tecnologias da vaga que ele já domina ou os conceitos correlacionados.
    """

    print(f"🤖 Analyzing job position with Gemini: {title}...")

    response = gemini_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "is_valid_match": types.Schema(type=types.Type.BOOLEAN),
                    "score": types.Schema(type=types.Type.INTEGER),
                    "justification": types.Schema(type=types.Type.STRING),
                    "adapted_summary": types.Schema(type=types.Type.STRING),
                    "adapted_skills": types.Schema(type=types.Type.STRING)
                },
                required=["is_valid_match", "score", "justification", "adapted_summary", "adapted_skills"]
            )
        )
    )
    return json.loads(response.text)


def process_and_save_job(title: str, company: str, link: str, description: str):
    """Analyzes the job and saves the data into Google Sheets if it's a good match."""
    try:
        # 1. Run the Gemini analysis
        analysis = analyze_job_position(title, description)
        
        # 2. Check if the job matches our Junior criteria
        if not analysis.get("is_valid_match"):
            print(f"❌ Job skipped (Low match score or wrong seniority). Score: {analysis.get('score')}")
            return

        print(f"🎯 Great match found! Score: {analysis.get('score')}. Connecting to Google Sheets...")
        
        # 3. Connect to the spreadsheet
        sheets_client = get_google_sheets_client()
        spreadsheet = sheets_client.open("jobs").sheet1
        
        # 4. Prepare the row data based on our columns:
        # Date | Title | Company | Link | Score | Status | Adapted_Summary | Adapted_Skills
        current_date = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        row_data = [
            current_date,
            title,
            company,
            link,
            int(analysis.get("score")),
            "Pending", # It stays 'Pending' until the daily report script sends the email
            analysis.get("adapted_summary"),
            analysis.get("adapted_skills")
        ]
        
        # 5. Append the new row to the sheet
        spreadsheet.append_row(row_data, value_input_option="USER_ENTERED")
        print("💾 Data successfully saved to Google Sheets!")
        
    except Exception as e:
        print(f"⚠️ An error occurred while processing the job: {e}")
        print("\n🔍 Error Details (Traceback):")
        traceback.print_exc()

# =====================================================================
# TESTING EXECUTION
# =====================================================================
if __name__ == "__main__":
    mock_title = "Developer Java Júnior (Spring Boot)"
    mock_company = "Sensedia"
    mock_link = "https://linkedin.com/jobs/view/test-junior-java-123"
    mock_description = """
    Estamos buscando um Dev Júnior apaixonado por tecnologia para integrar nosso time de engenharia.
    Você vai trabalhar criando APIs utilizando Java e Spring Boot.
    Requisitos:
    - Conhecimento em orientação a objetos com Java.
    - Noções de bancos de dados relacionais.
    - Noções de Docker.
    Oferecemos suporte e mentorias para acelerar sua carreira!
    """
    
    process_and_save_job(mock_title, mock_company, mock_link, mock_description)