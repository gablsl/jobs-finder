import os
import json
import time
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from google import genai
from google.genai import types
from google.genai.errors import APIError, ServerError

def load_user_config() -> dict:
    """Loads candidate preferences from local config.json or GitHub Environment Variables.
    
    Fails explicitly if no configuration source is found.
    """
    config_path = "config.json"
    
    # 1st Try: Looks for local file (Development Environment)
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    # 2nd Try: Looks for environment variable (GitHub Actions / Production)
    env_config = os.environ.get("USER_CONFIG_JSON")
    if env_config:
        return json.loads(env_config)
        
    # If neither source is found, explicitly raise an error informing the user
    raise FileNotFoundError(
        "❌ Critical Error: User settings not found!\n"
        "Make sure the 'config.json' file exists locally or that the "
        "environment variable 'USER_CONFIG_JSON' is set in the execution environment."
    )

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

def analyze_job_position(title: str, description: str, config: dict) -> dict:
    """Analyzes the job description based on a highly structured history of past experiences."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("⚠️ GEMINI_API_KEY environment variable not found.")
        
    gemini_client = genai.Client(api_key=api_key)
    clean_desc = description[:9000] if description else ""
    
    # Turns the list of stacks from the JSON into readable text for the prompt
    stacks_str = ", ".join(config.get("desired_stacks", []))
    
    # Builds a readable and structured text block of the candidate's professional history for the prompt
    past_experiences_blocks = []
    for exp in config.get("past_experiences", []):
        techs = ", ".join(exp.get("technologies", []))
        bullets = "\n".join([f"  - {b}" for b in exp.get("description", [])])
        
        block = (
            f"• Company: {exp.get('company')}\n"
            f"  Role: {exp.get('role')} ({exp.get('duration_months')} months)\n"
            f"  Technologies Used: {techs}\n"
            f"  Original Activities:\n{bullets}"
        )
        past_experiences_blocks.append(block)
        
    past_experiences_formatted = "\n\n".join(past_experiences_blocks)
    
    prompt = f"""
    Você é um recrutador técnico especialista e sistema de triagem ATS. 
    Avalie a compatibilidade da vaga de TI abaixo e adapte o histórico profissional do candidato para dar o máximo de match.
    
    DADOS DO CANDIDATO ATUAL:
    - Nome do Candidato: {config.get('candidate_name')}
    - Tecnologias de Interesse: {stacks_str}
    - Foco de Senioridade: {config.get('seniority_focus')}
    - Limite de Experiência Exigida: Máximo de {config.get('max_years_experience')} anos.
    
    HISTÓRICO PROFISSIONAL REAL DO CANDIDATO (Matéria-prima obrigatória):
    {past_experiences_formatted}

    REGRAS DE VALIDAÇÃO:
    - Se a vaga exigir tecnologias principais totalmente fora da lista de interesse informada, defina 'is_valid_match' as false.
    - Se a vaga exigir uma senioridade maior que a configurada (ex: Pleno sênior, Especialista, Lead), defina 'is_valid_match' as false.

    Vaga: {title}
    Descrição Bruta: {clean_desc}

    Gere uma resposta estritamente em formato JSON com os seguintes campos:
    - is_valid_match (boolean): true se a vaga estiver dentro do escopo.
    - score (int): nota de compatibilidade real de 0 a 100 baseado no nível configurado.
    
    - adapted_summary (string): Escreva um resumo profissional magnético focado para essa vaga, destacando as stacks que você domina que deem match com ela.
    
    - adapted_skills (string): Palavras-chave das tecnologias exigidas na vaga separadas por vírgula.
    
    - job_requirements (string): Um resumo estruturado e DETALHADO da descrição da vaga (atividades do dia a dia e pré-requisitos técnicos obrigatórios).
    
    - tailored_experiences (string): Pegue cada uma das empresas do 'HISTÓRICO PROFISSIONAL REAL' e reescreva os bullet points originais de suas atividades. Você deve adequar a escrita técnica dessas strings originais para destacar as necessidades, termos de engenharia e stacks dessa nova vaga (mantenha a verdade dos fatos e mantenha a separação por empresa, apenas eleve o tom técnico e o foco).
    """

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

    max_retries = 3
    delay = 5

    for attempt in range(max_retries):
        try:
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.2
                ),
            )
            return json.loads(response.text)
            
        except (ServerError, APIError) as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                print(f"⚠️ [Attempt {attempt + 1}/{max_retries}] Gemini unstable. Waiting {delay}s...")
                time.sleep(delay)
                delay *= 2
            else:
                raise e

    raise RuntimeError("❌ Unable to get response from Gemini after multiple attempts.")

def process_and_save_job(title: str, company: str, link: str, description: str):
    """Analyzes the job and saves the data into Google Sheets if it matches config criteria."""
    try:
        # Load dynamic user configuration (Local file or GitHub Environment Variable)
        config = load_user_config()
        
        # Pass the configuration dictionary to the Gemini analysis function
        analysis = analyze_job_position(title, description, config)
        
        raw_score = analysis.get("score", 0)
        try:
            score = int(raw_score.replace("%", "").strip()) if isinstance(raw_score, str) else int(raw_score)
        except Exception:
            score = 0
            
        is_valid = bool(analysis.get("is_valid_match", False))
        min_acceptable_score = config.get("min_match_score", 65)
        
        # Filter based on dynamic JSON value
        if not is_valid or score < min_acceptable_score:
            print(f"❌ Job discarded (Outside defined criteria). Title: {title} | Score: {score}%")
            return

        print(f"🎯 Compatible job found! Score: {score}%. Saving to spreadsheet...")
        
        sheets_client = get_google_sheets_client()
        sheet_name = os.environ.get("SPREADSHEET_NAME")
        spreadsheet = sheets_client.open(sheet_name).sheet1
        
        current_date = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        row_data = [
            current_date,
            title,
            company,
            link,
            score,
            "Pending",
            analysis.get("adapted_summary"),
            analysis.get("adapted_skills"),
            analysis.get("job_requirements"),
            analysis.get("tailored_experiences")
        ]
        
        spreadsheet.append_row(row_data, value_input_option="USER_ENTERED")
        print("💾 Saved successfully to Google Sheets!")
        
    except Exception as e:
        print(f"⚠️ Error processing job: {e}")