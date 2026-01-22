"""
map_conditions.py
=================

A module for generating Folium maps from snow station data.

This module handles:
- Creating custom SVG markers for wind direction.
- Generating Folium maps with multiple layers (HS, HN24, Wind, etc.).
- Applying dynamic radius and coloring (Green-Red-Black) based on values.
- Adding Colorbar legends.
- Saving the map to an HTML file.
"""

import folium
from folium import plugins
from folium.plugins import Geocoder
import branca.colormap as cm
import pandas as pd
from typing import List, Dict, Any

def create_svg_arrow(angle: float, speed: float) -> str:
    """
    Creates a simple SVG arrow icon rotated by 'angle'.
    """
    return f"""
    <div style="transform: rotate({angle}deg); width: 30px; height: 30px; 
                display: flex; align-items: center; justify-content: center;">
        <svg viewBox="0 0 24 24" width="30" height="30" 
             fill="black" stroke="white" stroke-width="1">
            <path d="M12 2L4.5 20.29L5.21 21L12 18L18.79 21L19.5 20.29L12 2Z" />
        </svg>
        <span style="position:absolute; bottom:-15px; font-weight:bold; 
                     background:white; padding:0 2px; border-radius:3px; 
                     font-size:10px; white-space: nowrap;">
            {speed:.1f} m/s
        </span>
    </div>
    """

def get_radius(value: float, max_value: float) -> float:
    """
    Calculates marker radius based on value relative to max.
    Range: 5 (min) to 15 (max).
    """
    if max_value <= 0:
        return 1000.0
    return 1000.0 + (value / max_value) * 2000.0

def add_map_title(m: folium.Map, timestamp: pd.Timestamp) -> None:
    """
    Adds a floating title with the last updated time.
    """
    # Format date (assuming UTC if not timezone aware, or display timezone name)
    tz_name = "UTC"
    if timestamp.tzinfo:
        tz_name = str(timestamp.tzinfo)
    
    date_str = timestamp.strftime('%Y-%m-%d %H:%M')
    
    title_html = f'''
        <div style="position: fixed;
                    top: 10px; right: 10px;
                    width: 280px; height: auto;
                    z-index:9999; font-size:16px;
                    background-color: rgba(255, 255, 255, 0.8);
                    border: 2px solid grey; border-radius: 5px;
                    padding: 10px; text-align: center; font-weight: bold;">
             Snow Conditions Map<br>
             <span style="font-size:14px; font-weight: normal;">
             Last Updated: {date_str} {tz_name}
             </span>
        </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

def add_legend_css(m: folium.Map) -> None:
    """
    Injects CSS to:
    1. Move the legend container down to avoid overlap with the title.
    2. Increase the font size of the color bar ticks and captions.
    """
    css = """
    <style>
        /* Move all controls in top-right down */
        .leaflet-top.leaflet-right {
            margin-top: 80px !important; 
        }

        /* Color Bar: Tick Labels (Numbers) */
        .leaflet-control svg .tick text {
            font-size: 14px !important;
            font-weight: 500;
        }
        
        /* Color Bar: Caption (Title) */
        .leaflet-control svg .caption {
            font-size: 16px !important;
            font-weight: bold;
        }
    </style>
    """
    m.get_root().html.add_child(folium.Element(css))


def add_zoom_aware_stroke(m: folium.Map) -> None:
    """
    Injects JavaScript to adjust circle border thickness (weight) 
    based on the zoom level. 
    Formula: weight = max(1, currentZoom / 3)
    """
    map_name = m.get_name()
    script = f"""
    <script>
    document.addEventListener("DOMContentLoaded", function() {{
        // Wait for the map to initialize
        var map = window.{map_name};
        
        if (map) {{
            function updateStrokeWeight() {{
                var zoom = map.getZoom();
                // Calculate new weight: Zoom 12->4px, Zoom 6->2px, Zoom 3->1px
                var newWeight = Math.max(1, zoom / 3); 
                
                map.eachLayer(function(layer) {{
                    // Target physical circles (L.Circle) but ignore other markers
                    if (layer instanceof L.Circle && !(layer instanceof L.CircleMarker)) {{
                        layer.setStyle({{ weight: newWeight }});
                    }}
                }});
            }}

            // Update on zoom end
            map.on('zoomend', updateStrokeWeight);
            
            // Run once on load to set initial state
            updateStrokeWeight();
        }}
    }});
    </script>
    """
    m.get_root().html.add_child(folium.Element(script))


def generate_map(stations_data: List[Dict[str, Any]], output_file: str = "snow_conditions_map.html") -> None:
    """
    Generates a layered Folium map from a list of station data dictionaries.
    """
    if not stations_data:
        print("No station data to map.")
        return

    # 1. Determine Max Values for Scaling
    # We need these to normalize the radius and set the colormap bounds
    max_hs = max((s['hs'] for s in stations_data), default=0)
    max_hn24 = max((s['hn24'] for s in stations_data), default=0)
    max_hn72 = max((s['hn72'] for s in stations_data), default=0)

    # Find the latest timestamp across all stations for the title
    latest_time = max((s['time'] for s in stations_data), default=pd.Timestamp.now())

    # Avoid zero-division or empty ranges
    max_hs = max(max_hs, 1.0)
    max_hn24 = max(max_hn24, 1.0)
    max_hn72 = max(max_hn72, 1.0)

    # 2. Define Colormaps
    colors = ['green', 'yellow', 'orange', 'red', 'black']
    
    # Create a linear colormap for each metric
    cmap_hs = cm.LinearColormap(colors, vmin=0, vmax=max_hs, caption="Total Snow (HS) [cm]")
    cmap_hn24 = cm.LinearColormap(colors, vmin=0, vmax=150, caption="New Snow 24h [cm]")
    cmap_hn72 = cm.LinearColormap(colors, vmin=0, vmax=100, caption="New Snow 72h [cm]")    

    # 3. Initialize Map
    center_lat = stations_data[0]['lat']
    center_lon = stations_data[0]['lon']
    m = folium.Map(location=[center_lat, center_lon], zoom_start=8, tiles="CartoDB positron")

    # Add Title and CSS fix
    add_map_title(m, latest_time)
    add_legend_css(m)

    # --- Add Additional Base Layers ---
    
    # Street map
    folium.TileLayer(
        'OpenStreetMap', 
        name='OpenStreetMap').add_to(m)

    # Topographic
    folium.TileLayer(
        'OpenTopoMap', 
        name='Topographic'
    ).add_to(m)

    # Satellite (Esri World Imagery)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite'
    ).add_to(m)

    # Add MiniMap
    minimap = plugins.MiniMap(toggle_display=True)
    m.add_child(minimap)

    # Add Colorbars to the map wrapped in divs with IDs for JS control
    # We'll add them via custom HTML instead of directly to control visibility
    cmap_hs_html = cmap_hs._repr_html_()
    cmap_hn24_html = cmap_hn24._repr_html_()
    cmap_hn72_html = cmap_hn72._repr_html_()

    colorbar_html = f'''
    <style>
        .colorbar-container svg {{
            font-size: 16px !important;
        }}
        .colorbar-container svg .caption {{
            font-size: 18px !important;
            font-weight: bold !important;
        }}
        .colorbar-container svg .tick text {{
            font-size: 14px !important;
        }}
    </style>
    <div id="colorbar-hs" class="colorbar-container" style="position: fixed; top: 100px; left: 10px; z-index: 1000; background: rgba(255,255,255,0.8); padding: 5px; border-radius: 5px;">
        {cmap_hs_html}
    </div>
    <div id="colorbar-hn24" class="colorbar-container" style="position: fixed; top: 100px; left: 10px; z-index: 1000; display: none; background: rgba(255,255,255,0.8); padding: 5px; border-radius: 5px;">
        {cmap_hn24_html}
    </div>
    <div id="colorbar-hn72" class="colorbar-container" style="position: fixed; top: 100px; left: 10px; z-index: 1000; display: none; background: rgba(255,255,255,0.8); padding: 5px; border-radius: 5px;">
        {cmap_hn72_html}
    </div>
    '''
    m.get_root().html.add_child(folium.Element(colorbar_html))

    # 4. Create Feature Groups
    fg_hs = folium.FeatureGroup(name="Total Snow Height (HS)", show=True)
    fg_hn24 = folium.FeatureGroup(name="New Snow 24h", show=False)
    fg_hn72 = folium.FeatureGroup(name="New Snow 72h", show=False)
    fg_wind = folium.FeatureGroup(name="Wind Direction", show=False)

    # 5. Add Markers
    for s in stations_data:
        loc = [s['lat'], s['lon']]

        # Determine Rain Status for Line Color
        is_raining = s.get('is_raining', False)
        line_color = 'red' if is_raining else 'green'
        rain_text = "YES" if is_raining else "No"
        if is_raining:
            hn24swe = round(s.get('delta_swe', 0), 2)
            rain_str = f'.<br>Est. 24 hrs. rain: {hn24swe} mm'
        else:
            rain_str = ''
        
        popup_txt = f"""
        <div style="font-family: sans-serif; width: 180px;">
            <b>Elevation: {int(s['altitude'])} m</b><br>
            <span style="color: gray; font-size: 0.9em;">{s['time']}</span><hr>
            <b>HS:</b> {s['hs']:.1f} cm<br>
            <b>HN24:</b> {s['hn24']:.1f} cm<br>
            <b>HN72:</b> {s['hn72']:.1f} cm<br>
            <b>Rain (24h):</b> <span style="color:{line_color}; font-weight:bold;">{rain_text}{rain_str}</span><br>
            <b>Wind:</b> {s['vw']:.1f} m/s @ {s['dw']:.0f}°
        </div>
        """
        
        # Using folium.Circle (radius in meters) instead of CircleMarker (radius in pixels)
        
        # HS Marker
        folium.Circle(
            location=loc,
            radius=get_radius(s['hs'], max_hs),
            popup=folium.Popup(popup_txt, max_width=300),
            color=line_color,         # Border Color (Rain Status)
            weight=3,                 # Border Thickness
            fill=True,
            fill_color=cmap_hs(s['hs']),
            fill_opacity=0.7,
            tooltip=f"Elevation: {int(s['altitude'])} m<br>HS: {s['hs']:.0f}cm"
        ).add_to(fg_hs)

        # HN24 Marker
        folium.Circle(
            location=loc,
            radius=get_radius(s['hn24'], max_hn24),
            popup=folium.Popup(popup_txt, max_width=300),
            color=line_color,         # Border Color (Rain Status)
            weight=3,                 # Border Thickness
            fill=True,
            fill_color=cmap_hn24(min(s['hn24'], 100)),
            fill_opacity=0.7,
            tooltip=f"HN24: {s['hn24']:.0f}cm"
        ).add_to(fg_hn24)
        
        # HN72 Marker
        folium.Circle(
            location=loc,
            radius=get_radius(s['hn72'], max_hn72),
            popup=folium.Popup(popup_txt, max_width=300),
            color=line_color,         # Border Color (Rain Status)
            weight=3,                 # Border Thickness
            fill=True,
            fill_color=cmap_hn72(min(s['hn72'], 150)),
            fill_opacity=0.7,
            tooltip=f"HN72: {s['hn72']:.0f}cm"
        ).add_to(fg_hn72)

        # Wind Arrow
        icon_html = create_svg_arrow(s['dw'], s['vw'])
        folium.Marker(
            location=loc,
            icon=folium.DivIcon(html=icon_html),
            tooltip=f"Wind: {s['vw']} m/s"
        ).add_to(fg_wind)

    # 6. Add Layers to Map
    fg_hs.add_to(m)
    fg_hn24.add_to(m)
    fg_hn72.add_to(m)
    fg_wind.add_to(m)

    # Add the Geocoder (search bar) to the map - position topleft to avoid overlap
    Geocoder(provider='photon', position="topleft").add_to(m)

    # CSS to position search bar next to zoom controls
    custom_css = """
    <style>
        .leaflet-control-geocoder {
            position: fixed !important;
            top: 10px !important;
            left: 55px !important;
            margin: 0 !important;
        }
        .leaflet-control-geocoder.leaflet-control-geocoder-expanded {
            width: 300px !important;
        }
    </style>
    """
    m.get_root().html.add_child(folium.Element(custom_css))

    folium.LayerControl(position='bottomright', collapsed=False, ).add_to(m)
    
    # 7. Inject Zoom-Aware Stroke Logic
    add_zoom_aware_stroke(m)

    # 8. Add JavaScript to switch colorbars based on active layer
    map_name = m.get_name()
    colorbar_switch_js = f'''
    <script>
    document.addEventListener("DOMContentLoaded", function() {{
        var map = window.{map_name};

        if (map) {{
            // Layer name to colorbar ID mapping
            var layerColorbarMap = {{
                "Total Snow Height (HS)": "colorbar-hs",
                "New Snow 24h": "colorbar-hn24",
                "New Snow 72h": "colorbar-hn72"
            }};

            // Track which data layers are currently active
            var activeLayers = new Set(["Total Snow Height (HS)"]);  // HS is shown by default

            function updateColorbar() {{
                // Hide all colorbars first
                document.querySelectorAll('.colorbar-container').forEach(function(el) {{
                    el.style.display = 'none';
                }});

                // Show colorbar for the most recently added layer (last in set)
                var layersArray = Array.from(activeLayers);
                if (layersArray.length > 0) {{
                    var lastLayer = layersArray[layersArray.length - 1];
                    var colorbarId = layerColorbarMap[lastLayer];
                    if (colorbarId) {{
                        var el = document.getElementById(colorbarId);
                        if (el) el.style.display = 'block';
                    }}
                }}
            }}

            // Listen for layer add events
            map.on('overlayadd', function(e) {{
                if (layerColorbarMap[e.name]) {{
                    activeLayers.add(e.name);
                    updateColorbar();
                }}
            }});

            // Listen for layer remove events
            map.on('overlayremove', function(e) {{
                if (layerColorbarMap[e.name]) {{
                    activeLayers.delete(e.name);
                    updateColorbar();
                }}
            }});

            // Initial update
            updateColorbar();
        }}
    }});
    </script>
    '''
    m.get_root().html.add_child(folium.Element(colorbar_switch_js))

    m.save(output_file)
    print(f"✅ Map saved to {output_file}")