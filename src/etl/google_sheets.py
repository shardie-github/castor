"""
DELTA:20251113_064143 Google Sheets Import Module

Optional Google Sheets import functionality for ETL fallback.
Requires Google API credentials configured.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from src.etl.csv_importer import MetricsDailyRow, CSVImporter

logger = logging.getLogger(__name__)

# Check if Google Sheets API is available
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    logger.warning("Google Sheets API not available. Install gspread and google-auth to enable.")


class GoogleSheetsImporter:
    """DELTA:20251113_064143 Google Sheets importer"""
    
    def __init__(
        self,
        csv_importer: CSVImporter,
        credentials_path: Optional[str] = None
    ):
        """
        Initialize Google Sheets importer
        
        Args:
            csv_importer: CSVImporter instance for parsing/importing
            credentials_path: Path to Google service account JSON credentials
        """
        if not GOOGLE_SHEETS_AVAILABLE:
            raise ImportError("Google Sheets API not available. Install gspread and google-auth.")
        
        self.csv_importer = csv_importer
        self.credentials_path = credentials_path or os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
        
        if not self.credentials_path:
            raise ValueError("Google Sheets credentials path not provided")
        
        # Initialize Google Sheets client
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """DELTA:20251113_064143 Initialize Google Sheets client"""
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=scopes
            )
            self._client = gspread.authorize(creds)
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            raise
    
    async def import_from_sheet(
        self,
        spreadsheet_id: str,
        worksheet_name: str = "Sheet1",
        range_name: Optional[str] = None,
        tenant_id: str = None,
        source: str = "google_sheets"
    ) -> Dict[str, Any]:
        """
        DELTA:20251113_064143 Import metrics from Google Sheet
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            worksheet_name: Name of worksheet to import
            range_name: Optional range (e.g., "A1:Z1000")
            tenant_id: Tenant ID for import
            source: Source identifier
            
        Returns:
            Import result dictionary
        """
        try:
            # Open spreadsheet
            spreadsheet = self._client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            # Get values
            if range_name:
                values = worksheet.get(range_name)
            else:
                values = worksheet.get_all_values()
            
            if not values or len(values) < 2:
                raise ValueError("Sheet is empty or missing header row")
            
            # Parse header
            header = values[0]
            expected_headers = ['day', 'episode_id', 'source', 'downloads', 'listeners', 
                              'completion_rate', 'ctr', 'conversions', 'revenue_cents']
            
            # Validate header
            if not all(h in header for h in expected_headers[:3]):  # At least required fields
                raise ValueError(f"Invalid header. Expected: {expected_headers}")
            
            # Convert to CSV format
            csv_lines = [','.join(header)]
            for row in values[1:]:
                if any(cell.strip() for cell in row):  # Skip empty rows
                    csv_lines.append(','.join(str(cell) if cell else '' for cell in row))
            
            csv_content = '\n'.join(csv_lines)
            
            # Parse and import using CSV importer
            rows = await self.csv_importer.parse_csv(csv_content)
            
            # Track import
            import_id = await self.csv_importer.track_import(
                tenant_id=tenant_id,
                source=source,
                file_name=f"{spreadsheet_id}/{worksheet_name}",
                status='processing',
                records_imported=0,
                records_failed=0
            )
            
            # Import to database
            result = await self.csv_importer.import_to_listener_metrics(
                rows=rows,
                tenant_id=tenant_id,
                import_id=import_id
            )
            
            # Update import status
            await self.csv_importer.update_import_status(
                import_id=import_id,
                status='completed',
                records_imported=result['imported'],
                records_failed=result['failed']
            )
            
            return {
                'import_id': import_id,
                'status': 'completed',
                'records_imported': result['imported'],
                'records_failed': result['failed'],
                'source': f"google_sheets:{spreadsheet_id}/{worksheet_name}"
            }
        
        except Exception as e:
            logger.error(f"Google Sheets import failed: {e}", exc_info=True)
            # Update import status if import_id exists
            if 'import_id' in locals():
                await self.csv_importer.update_import_status(
                    import_id=import_id,
                    status='failed',
                    records_imported=0,
                    records_failed=0,
                    error_message=str(e)
                )
            raise
