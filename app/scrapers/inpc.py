import requests
import pandas as pd
import camelot
import os
import re
from io import BytesIO

def get_pdf_link(page_url):
    """Extract PDF link from the webpage."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(page_url, headers=headers, timeout=20)
        
        # Look for PDF links in the HTML
        pdf_match = re.search(r'https?://[^\s"\'<>]+?\.pdf', response.text)
        if pdf_match:
            return pdf_match.group(0)
        
        # Alternative: look for WordPress upload links
        wp_match = re.search(r'href=["\']([^"\']*wp-content/uploads/[^"\']*\.pdf)["\']', response.text)
        if wp_match:
            url = wp_match.group(1)
            if not url.startswith('http'):
                # Make it absolute
                from urllib.parse import urljoin
                url = urljoin(page_url, url)
            return url
            
        return None
    except Exception as e:
        print(f"Error finding PDF link: {e}")
        return None

def extract_inpc_table(pdf_url):
    """Extract Tableau 2 from the INPC PDF."""
    temp_path = "/tmp/inpc_temp.pdf"
    
    # Check if PDF is already mounted locally
    if os.path.exists("/tmp/inpc.pdf"):
        print("Using local mounted PDF file")
        temp_path = "/tmp/inpc.pdf"
        skip_download = True
    else:
        skip_download = False
    
    try:
        if not skip_download:
            # Download PDF with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/pdf,*/*'
            }
            
            print(f"Downloading PDF from: {pdf_url}")
            response = requests.get(pdf_url, headers=headers, timeout=30, allow_redirects=True)
            
            # Check if we actually got a PDF
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower() and not response.content.startswith(b'%PDF'):
                print(f"Warning: Response is not a PDF (content-type: {content_type})")
                print(f"First 100 bytes: {response.content[:100]}")
                return None
            
            # Save to file
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            print(f"PDF downloaded successfully ({len(response.content)} bytes)")
        else:
            print(f"Using mounted PDF at {temp_path}")
        
        # Try lattice mode first (for tables with visible borders)
        try:
            print("Attempting extraction with lattice mode...")
            tables = camelot.read_pdf(
                temp_path, 
                pages='2',
                flavor='lattice',
                strip_text='\n'
            )
            
            if tables and len(tables) > 0:
                print(f"Found {len(tables)} table(s) with lattice mode")
                # Find table with most columns (likely Tableau 2)
                best_table = max(tables, key=lambda t: t.df.shape[1])
                print(f"Selected table with shape: {best_table.df.shape}")
                return best_table.df
        except Exception as e:
            print(f"Lattice mode failed: {e}")
        
        # Fallback to stream mode
        try:
            print("Attempting extraction with stream mode...")
            tables = camelot.read_pdf(
                temp_path,
                pages='2',
                flavor='stream',
                edge_tol=50,
                strip_text='\n'
            )
            
            if tables and len(tables) > 0:
                print(f"Found {len(tables)} table(s) with stream mode")
                # Find the largest table
                best_table = max(tables, key=lambda t: t.df.shape[0] * t.df.shape[1])
                print(f"Selected table with shape: {best_table.df.shape}")
                return best_table.df
        except Exception as e:
            print(f"Stream mode failed: {e}")
        
        return None
        
    except Exception as e:
        print(f"Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if os.path.exists(temp_path) and not skip_download:
            os.remove(temp_path)

def clean_inpc(df):
    """Q3.4: Data Wrangling for INPC Tableau 2."""
    if df is None or df.empty: 
        return None
    
    df = df.copy()
    
    # 1. Drop completely empty rows and columns
    df = df.dropna(how='all')
    df = df.dropna(axis=1, how='all')
    
    # 2. Reset index
    df = df.reset_index(drop=True)
    
    # 3. Strip whitespace from all cells
    for col in df.columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    
    # 4. Replace empty strings with NaN
    df = df.replace('', pd.NA)
    
    # 5. Clean numeric values: replace comma with dot for French decimal notation
    for col in df.columns:
        df[col] = df[col].apply(lambda x: str(x).replace(',', '.') if pd.notna(x) and isinstance(x, str) else x)
    
    # 6. If first row looks like header, set it as header
    if df.iloc[0].notna().all() or df.iloc[0].notna().sum() > df.shape[1] * 0.5:
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)
    
    return df