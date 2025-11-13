/**
 * DELTA:20251113T114706Z Google Apps Script for Metrics Daily Sync
 * 
 * Syncs metrics_daily data from Google Sheets to Supabase/PostgreSQL via REST API.
 * 
 * Setup:
 * 1. Open Google Sheets → Extensions → Apps Script
 * 2. Paste this script
 * 3. Set script properties:
 *    - SUPABASE_URL: Your Supabase project URL (e.g., https://xxxxx.supabase.co)
 *    - SUPABASE_KEY: Your Supabase anon/service_role key
 * 4. Add "Sync" menu → Run syncMetricsDaily()
 * 
 * Usage:
 * - Add "Sync" menu to Sheets: onOpen() creates menu automatically
 * - Click "Sync" → "Push Metrics Daily" to sync current sheet data
 * 
 * Sheet Format (first row as headers):
 * day,episode_id,source,downloads,listeners,completion_rate,ctr,conversions,revenue_cents
 */

// Configuration - Set via Script Properties
const SUPABASE_URL = PropertiesService.getScriptProperties().getProperty('SUPABASE_URL') || '';
const SUPABASE_KEY = PropertiesService.getScriptProperties().getProperty('SUPABASE_KEY') || '';

/**
 * Create custom menu on sheet open
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Sync')
    .addItem('Push Metrics Daily', 'syncMetricsDaily')
    .addToUi();
}

/**
 * Main sync function
 * Reads data from active sheet and pushes to Supabase
 */
function syncMetricsDaily() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  if (data.length < 2) {
    SpreadsheetApp.getUi().alert('No data to sync. Add data rows below headers.');
    return;
  }
  
  // Validate configuration
  if (!SUPABASE_URL || !SUPABASE_KEY) {
    SpreadsheetApp.getUi().alert('Error: SUPABASE_URL and SUPABASE_KEY must be set in Script Properties.');
    return;
  }
  
  // Parse headers (first row)
  const headers = data[0];
  const expectedHeaders = ['day', 'episode_id', 'source', 'downloads', 'listeners', 'completion_rate', 'ctr', 'conversions', 'revenue_cents'];
  
  // Validate headers
  const headerMap = {};
  expectedHeaders.forEach((h, i) => {
    const idx = headers.indexOf(h);
    if (idx === -1) {
      SpreadsheetApp.getUi().alert(`Error: Missing required column: ${h}`);
      return;
    }
    headerMap[h] = idx;
  });
  
  // Parse data rows
  const rows = [];
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    if (row.every(cell => cell === '')) continue; // Skip empty rows
    
    const rowData = {
      day: row[headerMap['day']],
      episode_id: row[headerMap['episode_id']],
      source: row[headerMap['source']],
      downloads: row[headerMap['downloads']] || null,
      listeners: row[headerMap['listeners']] || null,
      completion_rate: row[headerMap['completion_rate']] || null,
      ctr: row[headerMap['ctr']] || null,
      conversions: row[headerMap['conversions']] || null,
      revenue_cents: row[headerMap['revenue_cents']] || null
    };
    
    rows.push(rowData);
  }
  
  if (rows.length === 0) {
    SpreadsheetApp.getUi().alert('No valid data rows found.');
    return;
  }
  
  // Push to Supabase
  const url = `${SUPABASE_URL}/rest/v1/metrics_daily`;
  const options = {
    method: 'POST',
    headers: {
      'apikey': SUPABASE_KEY,
      'Authorization': `Bearer ${SUPABASE_KEY}`,
      'Content-Type': 'application/json',
      'Prefer': 'resolution=merge-duplicates' // Upsert mode
    },
    payload: JSON.stringify(rows)
  };
  
  try {
    const response = UrlFetchApp.fetch(url, options);
    const statusCode = response.getResponseCode();
    
    if (statusCode >= 200 && statusCode < 300) {
      SpreadsheetApp.getUi().alert(`Success! Synced ${rows.length} rows to metrics_daily.`);
    } else {
      const errorText = response.getContentText();
      SpreadsheetApp.getUi().alert(`Error ${statusCode}: ${errorText}`);
    }
  } catch (e) {
    SpreadsheetApp.getUi().alert(`Sync failed: ${e.toString()}`);
  }
}

/**
 * Set script properties (run once to configure)
 */
function setupScriptProperties() {
  const ui = SpreadsheetApp.getUi();
  
  const supabaseUrlResponse = ui.prompt('Enter Supabase URL:', ui.ButtonSet.OK_CANCEL);
  if (supabaseUrlResponse.getSelectedButton() === ui.Button.OK) {
    PropertiesService.getScriptProperties().setProperty('SUPABASE_URL', supabaseUrlResponse.getResponseText());
  }
  
  const supabaseKeyResponse = ui.prompt('Enter Supabase Key:', ui.ButtonSet.OK_CANCEL);
  if (supabaseKeyResponse.getSelectedButton() === ui.Button.OK) {
    PropertiesService.getScriptProperties().setProperty('SUPABASE_KEY', supabaseKeyResponse.getResponseText());
  }
  
  ui.alert('Script properties configured!');
}
