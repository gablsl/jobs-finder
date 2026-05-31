import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
# Importa a função do seu arquivo main.py
from main import process_and_save_job

def fetch_remotar_junior_jobs():
    """Scrapes junior tech jobs using Playwright and processes them through the pipeline."""
    url = "https://remotar.com.br/search/jobs?q=&c=13&t=17"
    
    print(f"🌐 Opening Remotar with Playwright: {url}...")
    
    # Inicia a instância do navegador em modo headless (segundo plano)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Navega até a URL e espera a rede ficar ociosa
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Espera especificamente a classe dos links de vaga carregar na tela
            print("⏳ Waiting for job cards to load...")
            page.wait_for_selector("a.job-title", timeout=10000)
            
            # Captura o HTML totalmente renderizado pelo JavaScript
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Encontra todos os elementos de vaga com a classe alvo
            job_elements = soup.find_all('a', class_='job-title')
            print(f"🎯 Found {len(job_elements)} job elements with class 'job-title'!")
            
            # Limpa e organiza a lista para evitar duplicatas
            job_list = []
            for element in job_elements:
                link = element.get('href')
                title = element.get_text().strip()
                if link and link not in [j['link'] for j in job_list]:
                    if not link.startswith("https"):
                        link = f"https://remotar.com.br{link}"
                    job_list.append({"title": title, "link": link})
            
            processed_count = 0
            
            # Varre cada uma das vagas encontradas
            for job in job_list:
                print(f"\n🟢 Navigating to job details: {job['title']}")
                
                # Abre a página interna da vaga para pegar a descrição completa
                page.goto(job['link'], wait_until="networkidle", timeout=20000)
                internal_html = page.content()
                internal_soup = BeautifulSoup(internal_html, 'html.parser')
                
                # Extrai o texto bruto da página para a análise do Gemini
                description = internal_soup.get_text()
                
                # Tenta extrair o nome da empresa através dos metadados da página
                company = "Remotar Partner"
                meta_desc = internal_soup.find('meta', property='og:description')
                if meta_desc:
                    meta_text = meta_desc['content']
                    if 'na empresa' in meta_text:
                        company = meta_text.split('na empresa')[-1].strip().split('.')[0]
                
                # 🚀 Envia a vaga para o pipeline (Gemini + Google Sheets)
                process_and_save_job(
                    title=job['title'],
                    company=company,
                    link=job['link'],
                    description=description
                )
                processed_count += 1
                
                # ⏳ DELAY DE SEGURANÇA: Espera 4 segundos para não estourar os 15 RPM do Gemini
                print("💤 Sleeping for 4 seconds to respect Gemini API rate limits...")
                time.sleep(4)
                
            print(f"\n📊 Scraping finished. Total jobs processed: {processed_count}")
            
        except Exception as e:
            print(f"⚠️ An error occurred during page processing: {e}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    fetch_remotar_junior_jobs()