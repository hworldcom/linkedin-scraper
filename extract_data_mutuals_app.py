import asyncio
import pandas as pd
from openpyxl import Workbook
from extract_data_company_utils import WebCrawler
from extract_data_company_utils import extract_data_names_urls
import pandas as pd
from typing import Dict
import random

# List of companies to process
#PROFILE_URLS = ["https://www.linkedin.com/in/marlongrayprofile","https://www.linkedin.com/in/a7meds3d/"]
#PROFILE_URL= "https://www.linkedin.com/in/marlongrayprofile"

async def main():

    #todo: initialize agent
    await process_excel_mutuals("rethink_connections.xlsx", "rethink_connections_updated.xlsx")

    print("extracted")

async def find_mutual_connections(crawlingAgent, PROFILE_URL):

    await crawlingAgent.start_process(PROFILE_URL)
    try:
        # Try locating with short timeout
        mutual_button = await crawlingAgent.locate("a:has-text('mutual connection')")
    except:
        print("[!] Mutual connection button not found.")
        return [], []
    print("Mutual connection found for", PROFILE_URL)
    delay = random.uniform(2.5, 4)*1000
    print(f"Sleeping for {delay:.2f} ms...\n")

    await crawlingAgent.timeout(delay)
    await crawlingAgent.move_to_location(mutual_button)
    await crawlingAgent.click(mutual_button)

    profile_names = []
    profile_urls = []
    await extract_data_names_urls(crawlingAgent, profile_names, profile_urls)
    return profile_names, profile_urls


async def process_excel_mutuals(file_path: str, output_path: str):
    df = pd.read_excel(file_path)

    print("initializing agent... ")
    crawlingAgent = WebCrawler("https://www.linkedin.com/", WINDOW_OFFSET=90)
    await crawlingAgent.init()

    # Add columns if they don't already exist
    if "mutual_names" not in df.columns:
        df["mutual_names"] = ""
    if "mutual_urls" not in df.columns:
        df["mutual_urls"] = ""

    for i, url in enumerate(df["LinkedIn Profile"]):
        print(f"\n[{i+1}/{len(df)}] Processing URL: {url}")

        # Skip empty/invalid links
        if pd.isna(url) or not isinstance(url, str) or "linkedin.com/in/" not in url:
            print("[!] Skipping invalid or empty URL")
            continue

        try:
            names, urls = await find_mutual_connections(crawlingAgent, url)

            # Write directly to the DataFrame row
            df.loc[i, "mutual_names"] = ", ".join(names)
            df.loc[i, "mutual_urls"] = ", ".join(urls)

        except Exception as e:
            df.loc[i, "mutual_names"] = f"Error: {e}"
            df.loc[i, "mutual_urls"] = ""

        # Random delay between rows
        delay = random.uniform(3, 7)
        print(f"Sleeping for {delay:.2f} seconds...\n")
        await asyncio.sleep(delay)

    # Save the updated DataFrame
    df.to_excel(output_path, index=False)
    print(f"[✓] Data written to {output_path}")


asyncio.run(main())
