import requests
import pandas as pd

def scrape_budget(url, timeout=20):
    # API endpoint discovered from the site's network traffic
    api_url = "https://services.tresor.mr/api/v1/budget-execution"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(api_url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def clean_budget(df):
    if df.empty: return df
    return df.dropna(how='all').reset_index(drop=True)