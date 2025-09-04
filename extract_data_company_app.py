import asyncio
import pandas as pd
from openpyxl import Workbook

# Import your scraping function
from extract_data_company_utils import extract_data_urls_names_company  # Make sure path is correct
from extract_data_company_utils import WebCrawler
# List of companies to process
#companies = ["covivio","banxware"]
companies = ["banxware"]

async def main():
    # Create a Pandas Excel writer object using openpyxl engine
    URL = "https://www.linkedin.com/"
    crawlingAgent = WebCrawler(URL, WINDOW_OFFSET=90)
    await crawlingAgent.init()
    with pd.ExcelWriter("linkedin_profiles.xlsx", engine="openpyxl") as writer:
        for company in companies:
            print(f"🔍 Extracting for: {company}")
            try:
                await crawlingAgent.safe_goto(URL)
                profile_names, profile_urls = await extract_data_urls_names_company(crawlingAgent, company)
                data = {
                    "name": profile_names,
                    "linkedin_url": profile_urls
                }
                df = pd.DataFrame(data)
                # Write to a new sheet named after the company (limited to 31 characters)
                df.to_excel(writer, sheet_name=company[:31], index=False)
                print(f"✅ Done: {company}, found {len(profile_names)} profiles")
            except Exception as e:
                print(f"❌ Failed to process {company}: {e}")

asyncio.run(main())
