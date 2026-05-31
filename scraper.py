import time
import os
import json
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import gspread
from google.oauth2.service_account import Credentials

# Importa a função do seu arquivo main.py
from main import process_and_save_job, get_google_sheets_client

def get_already_processed_links():
    """Connects to Google Sheets and fetches all job links already saved to avoid duplicates."""
    try:
        print("📊 Connecting to Google Sheets to check existing jobs...")
        sheets_client = get_google_sheets_client()
        spreadsheet = sheets_client.open("jobs").sheet1
        
        # col_values(4) grabs the 4th column (Link)
        # If the sheet is empty, it returns an empty list
        links = spreadsheet.col_values(4)
        print(f"📁 Found {len(links)} links already stored in your Google Sheets.")
        return links
    except Exception as e:
        print(f"⚠️ Warning: Could not read Google Sheets ({e}). Proceeding without cache history.")
        return []

def fetch_remotar_junior_jobs():
    """Scrapes junior tech jobs using Playwright and processes only NEW positions."""
    url = "https://remotar.com.br/search/jobs?q=&c=13&t=17"
    
    # 🎯 STEP 1: Fetch links that are already in the spreadsheet
    existing_links = get_already_processed_links()
    
    print(f"\n🌐 Opening Remotar with Playwright: {url}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            print("⏳ Waiting for job cards to load...")
            page.wait_for_selector("a.job-title", timeout=10000)
            
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            job_elements = soup.find_all('a', class_='job-title')
            print(f"🎯 Found {len(job_elements)} raw job elements on the page.")
            
            # Organize raw jobs from page
            job_list = []
            for element in job_elements:
                link = element.get('href')
                title = element.get_text().strip()
                if link:
                    if not link.startswith("https"):
                        link = f"https://remotar.com.br{link}"
                    if link not in [j['link'] for j in job_list]:
                        job_list.append({"title": title, "link": link})
            
            processed_count = 0
            
            # Varre as vagas encontradas
            for job in job_list:
                # 🎯 STEP 2: CHECK IF THE JOB IS ALREADY IN THE SHEET
                if job['link'] in existing_links:
                    print(f"⏭️ Skipping (Already Processed): {job['title']}")
                    continue
                
                print(f"\n🟢 New Job Found! Navigating to details: {job['title']}")
                
                page.goto(job['link'], wait_until="networkidle", timeout=20000)
                internal_html = page.content()
                internal_soup = BeautifulSoup(internal_html, 'html.parser')
                
                description = internal_soup.get_text()
                
                company = "Remotar Partner"
                meta_desc = internal_soup.find('meta', property='og:description')
                if meta_desc:
                    meta_text = meta_desc['content']
                    if 'na empresa' in meta_text:
                        company = meta_text.split('na empresa')[-1].strip().split('.')[0]
                
                # Sends ONLY fresh new jobs to Gemini + Sheets
                process_and_save_job(
                    title=job['title'],
                    company=company,
                    link=job['link'],
                    description=description
                )
                processed_count += 1
                
                print("💤 Sleeping for 4 seconds to respect Gemini API rate limits...")
                time.sleep(4)
                
            print(f"\n📊 Scraping finished. Total NEW jobs sent to pipeline: {processed_count}")
            
        except Exception as e:
            print(f"⚠️ An error occurred during page processing: {e}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    fetch_remotar_junior_jobs()