import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
# Import the function from main.py
from main import process_and_save_job

def fetch_remotar_junior_jobs():
    """Scrapes junior tech jobs using Playwright to handle JavaScript rendering."""
    url = "https://remotar.com.br/search/jobs?q=&c=13&t=17"
    
    print(f"🌐 Opening Remotar with Playwright: {url}...")
    
    # Starting the browser instance
    with sync_playwright() as p:
        # headless=True means it runs invisibly in the background
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Navigate to the page and wait until network is idle
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait specifically for our target class to be injected into the DOM
            print("⏳ Waiting for job cards to load...")
            page.wait_for_selector("a.job-title", timeout=10000)
            
            # Get the fully rendered HTML content
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all job links with the class you discovered
            job_elements = soup.find_all('a', class_='job-title')
            print(f"🎯 Found {len(job_elements)} job elements with class 'job-title'!")
            
            job_list = []
            for element in job_elements:
                link = element.get('href')
                title = element.get_text().strip()
                if link and link not in [j['link'] for j in job_list]:
                    if not link.startswith("https"):
                        link = f"https://remotar.com.br{link}"
                    job_list.append({"title": title, "link": link})
            
            processed_count = 0
            
            # Crawl each individual job page
            for job in job_list:
                print(f"\n🟢 Navigating to job details: {job['title']}")
                
                # Open the internal link in our browser instance
                page.goto(job['link'], wait_until="networkidle", timeout=20000)
                internal_html = page.content()
                internal_soup = BeautifulSoup(internal_html, 'html.parser')
                
                # Extract full text/description
                description = internal_soup.get_text()
                
                # Extract company name from metadata or layout
                company = "Remotar Partner"
                meta_desc = internal_soup.find('meta', property='og:description')
                if meta_desc:
                    meta_text = meta_desc['content']
                    if 'na empresa' in meta_text:
                        company = meta_text.split('na empresa')[-1].strip().split('.')[0]
                
                # 🚀 Send it to your Gemini + Google Sheets pipeline
                process_and_save_job(
                    title=job['title'],
                    company=company,
                    link=job['link'],
                    description=description
                )
                processed_count += 1
                time.sleep(1) # Friendly delay
                
            print(f"\n📊 Scraping finished. Total jobs processed: {processed_count}")
            
        except Exception as e:
            print(f"⚠️ An error occurred during page processing: {e}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    fetch_remotar_junior_jobs()