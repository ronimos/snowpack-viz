# Snowpack-Viz

An interactive web-based snow conditions map generator that visualizes SNOWPACK model output data. Currently configured for weather stations in Central Asia, but easily adaptable for any region.

## Features

- **Interactive Map**: Generates a Folium-based HTML map with multiple base layers (CartoDB, OpenStreetMap, Topographic, Satellite)
- **Snow Metrics Visualization**:
  - Total Snow Height (HS)
  - 24-hour New Snow (HN24)
  - 72-hour New Snow (HN72)
  - Wind Direction and Speed
- **Rain Detection**: Automatically flags stations where rain (vs. snow) was detected in the last 24 hours
- **Responsive Design**: Works on desktop browsers, tablets, and mobile devices
- **Dynamic Colorbar**: Shows the appropriate legend based on the selected data layer
- **Search Functionality**: Built-in geocoder for location search
- **Optional Publishing**: Upload generated maps to a remote server via SSH/SCP

## Installation

Requires Python 3.12+

```bash
# Clone the repository
git clone <repository-url>
cd snow_map

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Usage

### 1. Fetch Data (if using remote SNOWPACK server)

Edit `fetch_data.sh` and `smet_paths.txt` to configure your data source:

```bash
# fetch_data.sh - configure these variables:
REMOTE_USER="your_username"
REMOTE_HOST="your.server.com"
REMOTE_PORT="22"
LOCAL_DIR="./data"

# Run the fetch script
./fetch_data.sh
```

### 2. Generate the Map

```bash
# Process all .smet files in the data folder
python src/snow_map/main.py --folder ./data

# Or specify individual files
python src/snow_map/main.py --files station1.smet station2.smet

# Custom output file
python src/snow_map/main.py --folder ./data --output my_map.html
```

### 3. View the Map

Open the generated `snow_conditions_map.html` in any web browser.

### Quick Update (All-in-One)

Use the convenience script to fetch data, generate the map, and publish in one command:

```bash
./update_snow_map.sh
```

Before running, edit the script to configure your remote server settings:

```bash
# update_snow_map.sh - configure these variables:
REMOTE_USER="your_username"
REMOTE_HOST="your.server.com"
REMOTE_PORT="22"
REMOTE_PATH="~/public_html/"  # Your web directory
```

This script is ideal for automation via cron job:

```bash
# Run every 6 hours
0 */6 * * * /path/to/snow_map/update_snow_map.sh >> /path/to/snow_map/update.log 2>&1
```

## Adapting for Different Regions

The map automatically centers on the first station in your dataset. To use this for a different region:

1. **Provide your SMET files**: Place your SNOWPACK `.smet` output files in the `data/` directory (or any folder you specify)

2. **Update data fetching** (if applicable): Modify `fetch_data.sh` with your server details and `smet_paths.txt` with the paths to your SMET files

3. **Adjust color scales** (optional): In `map_conditions.py`, you can modify the colormap ranges:
   ```python
   # Lines 171-173: Adjust vmax values based on your region's typical snow depths
   cmap_hs = cm.LinearColormap(colors, vmin=0, vmax=max_hs, caption="Total Snow (HS) [cm]")
   cmap_hn24 = cm.LinearColormap(colors, vmin=0, vmax=150, caption="New Snow 24h [cm]")
   cmap_hn72 = cm.LinearColormap(colors, vmin=0, vmax=100, caption="New Snow 72h [cm]")
   ```

## SMET File Format

The tool expects SNOWPACK `.smet` output files with the following key fields:

| Field | Description |
|-------|-------------|
| `station_id` | Unique station identifier |
| `station_name` | Station name |
| `latitude` | Station latitude |
| `longitude` | Station longitude |
| `altitude` | Station elevation (m) |
| `HS_mod` | Modeled snow height (cm) |
| `HN24` | 24-hour new snow height (cm) |
| `HN72_24` | 72-hour new snow (cm) |
| `HNW24` | 24-hour precipitation water equivalent (mm) |
| `SWE` | Snow water equivalent (kg/m², equiv. to mm) |
| `VW` | Wind velocity (m/s) |
| `DW` | Wind direction (degrees) |

## Rain Detection Logic

The tool detects rain events using the following criteria:
- Precipitation occurred (`HNW24 > 0`)
- Significant water increase (`delta_SWE > 5 mm`)
- Water increase exceeds reported precipitation (`delta_SWE > HNW24`)

When rain is detected, station markers display a red border instead of green.

## Publishing to Remote Server (Optional)

To automatically publish the generated map:

1. Create a `.env` file in `src/snow_map/`:
   ```
   SSH_HOST=your.server.com
   SSH_PORT=22
   SSH_USER=username
   SSH_KEY_PATH=/path/to/private/key
   REMOTE_PATH=/var/www/html/
   ```

2. Uncomment the publish line in `main.py`:
   ```python
   publish_file(args.output)
   ```

## Project Structure

```
snowpack-viz/
├── src/snowpack_viz/
│   ├── main.py           # CLI entry point
│   ├── read_smet.py      # SMET file parser
│   ├── map_conditions.py # Map generation
│   └── publish.py        # Remote publishing (Python)
├── data/                 # SMET files directory
├── fetch_data.sh         # Data download script
├── update_snowpack_viz.sh # All-in-one: fetch, generate, publish
├── smet_paths.txt        # List of remote SMET paths
└── pyproject.toml        # Project dependencies
```

## Dependencies

- **pandas**: Data processing
- **folium**: Interactive map generation
- **branca**: Colormap/legend support
- **paramiko/scp**: SSH/SCP for remote publishing (optional)

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
