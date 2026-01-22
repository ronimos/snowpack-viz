"""
read_smet.py
============

A module for parsing SNOWPACK .smet files.

This module handles:
- Reading metadata headers from .smet files.
- Parsing the time-series data into a Pandas DataFrame.
- Calculating derived metrics like 24h, 48h, and 72h snow accumulation.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Any, List

def parse_smet(file_path: Path) -> Tuple[Dict[str, str], pd.DataFrame]:
    """
    Parses a SNOWPACK .smet file into metadata and a Pandas DataFrame.

    Args:
        file_path (Path): Path to the .smet file.

    Returns:
        Tuple[Dict[str, str], pd.DataFrame]: A tuple containing a dictionary of 
        metadata and a DataFrame of the time-series data.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid.
    """
    metadata = {}
    header_end_line = 0
    
    if not file_path.exists():
        raise FileNotFoundError(f"SMET file not found: {file_path}")

    # 1. Parse Header
    with open(file_path, 'r') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if line == '[DATA]':
                header_end_line = i + 1
                break
            
            if '=' in line:
                key, val = line.split('=', 1)
                metadata[key.strip()] = val.strip()
            elif line.startswith('fields'):
                # Handle fields line which might not have '='
                parts = line.split()
                if len(parts) > 1:
                    metadata['fields'] = parts[1:] # Skip 'fields' keyword

    if 'fields' not in metadata:
        raise ValueError("SMET file missing 'fields' definition in header.")
    # 2. Parse Data
    try:
        df = pd.read_csv(
            file_path, 
            sep='\s+', #delim_whitespace=True, 
            skiprows=header_end_line, 
            header=None,
            #names=metadata['fields'],
        )
        df.columns = metadata['fields'].split(' ')
    except pd.errors.ParserError as e:
        raise ValueError(f"Error parsing SMET data lines: {e}")
    
    # Convert timestamp
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp').sort_index()
    else:
        raise ValueError("SMET data missing 'timestamp' column.")
    
    return metadata, df

def get_station_conditions(metadata: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculates latest HS, HN24, HN48, HN72, and Wind from the dataframe.

    Args:
        metadata (Dict[str, Any]): Metadata dictionary from parse_smet.
        df (pd.DataFrame): Time-series DataFrame from parse_smet.

    Returns:
        Dict[str, Any]: A dictionary containing processed station conditions.
    """
    if df.empty:
        return {}

    # Get the most recent valid row
    latest = df.iloc[-1]
    last_time = latest.name
    
    # 1. Total Snow Height (HS)
    # Prefer measured, fallback to modeled, default to 0
    hs_cm = latest.get('HS_mod', latest.get('HS_mean', 0))
    if hs_cm == -999: hs = 0

    # 2. New Snow (HN)
    # HN24 is usually a rolling 24h sum. 
    # For 48h and 72h, we look back in the time series.
    
    def get_past_val(col: str, hours_ago: int) -> float:
        """Helper to safely get a value from X hours ago."""
        try:
            target_time = last_time - pd.Timedelta(hours=hours_ago)
            # Find nearest index (using nearest to handle slight time misalignments)
            idx = df.index.get_indexer([target_time], method='nearest')[0]
            val = df.iloc[idx][col]
            return 0.0 if val == -999 else float(val)
        except (KeyError, IndexError):
            return 0.0

    hn24_cm = latest.get('HN24', 0)
    hn72_cm = latest.get('HN72_24', 0)
    if hn24_cm == -999: hn24_cm = 0
     

    # 3. Wind
    vw = latest.get('VW', 0) # Velocity m/s
    dw = latest.get('DW', 0) # Direction degrees
    
    # 4. Rain Detection
    # Logic: Raining if delta_SWE (24h) > delta_SH_mod (24h) AND delta_SWE > 0
    
    # Get SWE (Snow Water Equivalent) - usually kg/m^2 which is equiv to mm
    swe_now = latest.get('SWE', 0)
    if swe_now == -999: swe_now = 0
    swe_prev = get_past_val('SWE', 24)
    delta_swe = swe_now - swe_prev # swe is in kg/m^3, i.e., mm of water

    # Get 24h precipitation water equivalent (already in mm)
    hnw24 = latest.get('HNW24', 0)
    if hnw24 == -999: hnw24 = 0

    # Rain detection: precipitation occurred (hnw24 > 0), significant SWE increase (> 5mm),
    # and SWE increase exceeds reported precipitation (indicating rain absorbed into snowpack)
    is_raining = (hnw24 > 0) and (delta_swe > 5.0) and (delta_swe > hnw24)
 
    return {
        'id': metadata.get('station_id', 'Unknown'),
        'name': metadata.get('station_name', 'Unknown'),
        'lat': float(metadata.get('latitude', 0)),
        'lon': float(metadata.get('longitude', 0)),
        'altitude': float(metadata.get('altitude', 0)),
        'hs': hs_cm,
        'hn24': hn24_cm,
        'hn72': hn72_cm,
        'vw': vw,
        'dw': dw,
        'is_raining': is_raining,
        'delta_swe': delta_swe, 
        'time': last_time
    }