"""
TP4 DataOps - Pipeline unifié
Orchestre les 3 collectes (Budget, Football, INPC) et génère les métriques
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path

from scrapers.budget import scrape_budget, clean_budget
from scrapers.football import scrape_football, clean_football
from scrapers.inpc import get_pdf_link, extract_inpc_table, clean_inpc

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Variables d'environnement
OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/out')
BUDGET_URL = os.getenv('BUDGET_URL', 'https://services.tresor.mr/budget')
FOOTBALL_URL = os.getenv('FOOTBALL_URL', 'https://www.tntsports.co.uk/football/mauritanian-league/calendar-results.shtml')
INPC_PAGE_URL = os.getenv('INPC_PAGE_URL', 'https://ansade.mr/fr/note-mensuelle-de-lindice-national-des-prix-a-la-consommation-inpc-decembre-2025/')
HTTP_TIMEOUT = int(os.getenv('HTTP_TIMEOUT_SECONDS', '20'))


def ensure_output_dir():
    """Crée le dossier de sortie s'il n'existe pas"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ready: {OUTPUT_DIR}")


def run_budget_scraping(kpi):
    """Phase 1: Scraping Budget"""
    logger.info("=" * 60)
    logger.info("--- Phase 1: Budget Execution (Trésor) ---")
    
    source_name = "budget"
    kpi[source_name] = {
        "status": "FAIL",
        "rows_extracted": 0,
        "missing_values": 0,
        "timestamp": datetime.now().isoformat(),
        "error": None
    }
    
    try:
        # Scraping
        df_raw = scrape_budget(BUDGET_URL, timeout=HTTP_TIMEOUT)
        
        if df_raw is None or df_raw.empty:
            raise ValueError("No data extracted from budget source")
        
        logger.info(f"Budget: Extracted {len(df_raw)} raw rows")
        
        # Nettoyage
        df_clean = clean_budget(df_raw)
        
        if df_clean.empty:
            raise ValueError("Cleaning resulted in empty dataset")
        
        # Sauvegarde
        output_path = os.path.join(OUTPUT_DIR, 'budget_execution.csv')
        df_clean.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"Budget: Saved to {output_path}")
        
        # Métriques
        kpi[source_name]["status"] = "OK"
        kpi[source_name]["rows_extracted"] = len(df_clean)
        kpi[source_name]["missing_values"] = int(df_clean.isnull().sum().sum())
        kpi[source_name]["columns"] = list(df_clean.columns)
        
    except Exception as e:
        logger.error(f"Budget scraping failed: {str(e)}", exc_info=True)
        kpi[source_name]["error"] = str(e)


def run_football_scraping(kpi):
    """Phase 2: Scraping Football"""
    logger.info("=" * 60)
    logger.info("--- Phase 2: Football Results (TNT Sports) ---")
    
    source_name = "football"
    kpi[source_name] = {
        "status": "FAIL",
        "rows_extracted": 0,
        "missing_values": 0,
        "timestamp": datetime.now().isoformat(),
        "error": None
    }
    
    try:
        # Scraping
        df_raw = scrape_football(FOOTBALL_URL, timeout=HTTP_TIMEOUT)
        
        if df_raw is None or df_raw.empty:
            raise ValueError("No data extracted from football source")
        
        logger.info(f"Football: Extracted {len(df_raw)} raw rows")
        
        # Nettoyage
        df_clean = clean_football(df_raw)
        
        if df_clean.empty:
            raise ValueError("Cleaning resulted in empty dataset")
        
        # Sauvegarde
        output_path = os.path.join(OUTPUT_DIR, 'football_results.csv')
        df_clean.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"Football: Saved to {output_path}")
        
        # Métriques
        kpi[source_name]["status"] = "OK"
        kpi[source_name]["rows_extracted"] = len(df_clean)
        kpi[source_name]["missing_values"] = int(df_clean.isnull().sum().sum())
        kpi[source_name]["columns"] = list(df_clean.columns)
        
    except Exception as e:
        logger.error(f"Football scraping failed: {str(e)}", exc_info=True)
        kpi[source_name]["error"] = str(e)


def run_inpc_scraping(kpi):
    """Phase 3: Scraping INPC PDF"""
    logger.info("=" * 60)
    logger.info("--- Phase 3: INPC (PDF) ---")
    
    source_name = "inpc"
    kpi[source_name] = {
        "status": "FAIL",
        "rows_extracted": 0,
        "missing_values": 0,
        "timestamp": datetime.now().isoformat(),
        "error": None,
        "pdf_url": None
    }
    
    try:
        # Récupération du lien PDF
        pdf_url = get_pdf_link(INPC_PAGE_URL, timeout=HTTP_TIMEOUT)
        
        if not pdf_url:
            raise ValueError("Could not find PDF link on INPC page")
        
        logger.info(f"Found PDF: {pdf_url}")
        kpi[source_name]["pdf_url"] = pdf_url
        
        # Extraction du tableau
        df_raw = extract_inpc_table(pdf_url, timeout=HTTP_TIMEOUT)
        
        if df_raw is None or df_raw.empty:
            raise ValueError("Could not extract table from PDF")
        
        logger.info(f"INPC: Extracted {len(df_raw)} rows from Tableau 2")
        
        # Nettoyage
        df_clean = clean_inpc(df_raw)
        
        if df_clean.empty:
            raise ValueError("Cleaning resulted in empty dataset")
        
        # Sauvegarde
        output_path = os.path.join(OUTPUT_DIR, 'inpc_table2.csv')
        df_clean.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"INPC: Saved to {output_path}")
        
        # Métriques
        kpi[source_name]["status"] = "OK"
        kpi[source_name]["rows_extracted"] = len(df_clean)
        kpi[source_name]["missing_values"] = int(df_clean.isnull().sum().sum())
        kpi[source_name]["columns"] = list(df_clean.columns)
        
    except Exception as e:
        logger.error(f"INPC scraping failed: {str(e)}", exc_info=True)
        kpi[source_name]["error"] = str(e)


def generate_kpi_json(kpi):
    """Génère le fichier kpi.json"""
    kpi_path = os.path.join(OUTPUT_DIR, 'kpi.json')
    
    # Ajout de métadonnées globales
    kpi["pipeline"] = {
        "execution_timestamp": datetime.now().isoformat(),
        "total_sources": 3,
        "successful_sources": sum(1 for k, v in kpi.items() if k != "pipeline" and v.get("status") == "OK"),
        "failed_sources": sum(1 for k, v in kpi.items() if k != "pipeline" and v.get("status") == "FAIL")
    }
    
    with open(kpi_path, 'w', encoding='utf-8') as f:
        json.dump(kpi, f, indent=2, ensure_ascii=False)
    
    logger.info(f"KPI metrics saved to {kpi_path}")


def generate_run_report(kpi):
    """Génère le fichier run_report.md"""
    report_path = os.path.join(OUTPUT_DIR, 'run_report.md')
    
    successful = kpi["pipeline"]["successful_sources"]
    failed = kpi["pipeline"]["failed_sources"]
    
    lines = [
        "# Pipeline Execution Report",
        "",
        f"**Execution Time:** {kpi['pipeline']['execution_timestamp']}",
        "",
        "## Summary",
        f"- Total sources: {kpi['pipeline']['total_sources']}",
        f"- Successful: {successful}",
        f"- Failed: {failed}",
        "",
        "## Details by Source",
        ""
    ]
    
    for source in ["budget", "football", "inpc"]:
        if source in kpi:
            info = kpi[source]
            lines.append(f"### {source.upper()}")
            lines.append(f"- **Status:** {info['status']}")
            lines.append(f"- **Rows extracted:** {info['rows_extracted']}")
            lines.append(f"- **Missing values:** {info['missing_values']}")
            
            if info.get('error'):
                lines.append(f"- **Error:** {info['error']}")
            
            if source == "inpc" and info.get('pdf_url'):
                lines.append(f"- **PDF URL:** {info['pdf_url']}")
            
            lines.append("")
    
    lines.append("## Output Files")
    lines.append("- `budget_execution.csv`")
    lines.append("- `football_results.csv`")
    lines.append("- `inpc_table2.csv`")
    lines.append("- `kpi.json`")
    lines.append("- `run_report.md`")
    lines.append("")
    
    if failed > 0:
        lines.append("## Notes")
        lines.append(f"⚠️ {failed} source(s) failed. Check errors above.")
    else:
        lines.append("## Notes")
        lines.append("✅ All sources scraped successfully!")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    logger.info(f"Run report saved to {report_path}")


def main():
    """Point d'entrée principal du pipeline"""
    logger.info("=" * 60)
    logger.info("TP4 DataOps Pipeline - Starting")
    logger.info("=" * 60)
    
    # Préparation
    ensure_output_dir()
    
    # Dictionnaire de métriques KPI
    kpi = {}
    
    # Exécution des 3 phases (indépendantes)
    run_budget_scraping(kpi)
    run_football_scraping(kpi)
    run_inpc_scraping(kpi)
    
    # Génération des fichiers de sortie
    logger.info("=" * 60)
    logger.info("--- Generating KPI and Report ---")
    generate_kpi_json(kpi)
    generate_run_report(kpi)
    
    # Résumé final
    logger.info("=" * 60)
    logger.info("Pipeline execution completed!")
    logger.info(f"Successful: {kpi['pipeline']['successful_sources']}/3")
    logger.info(f"Failed: {kpi['pipeline']['failed_sources']}/3")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()