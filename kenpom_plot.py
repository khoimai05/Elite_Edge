"""
KenPom Team Ratings Visualization Script
Fetches data from KenPom API and creates a Plotly visualization
"""
import pandas as pd
import os
import requests
import numpy as np
from matplotlib.path import Path as MPLPath
import plotly.graph_objects as go
from dotenv import load_dotenv
from datetime import datetime
import plotly.io as pio
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def fetch_kenpom_data(year):
    """
    Fetch team ratings data from KenPom API
    
    Args:
        year: Season year (ending year of the season, e.g., 2025 = 2024-25 season)
    
    Returns:
        DataFrame with team ratings data
    """
    BASE_URL = "https://kenpom.com/api.php"
    
    # Try to get API key from environment variables first
    API_KEY = os.getenv('KENPOM_API_KEY')
    
    # If not found, try to get from Airflow Variables (if running in Airflow)
    if not API_KEY:
        try:
            from airflow.models import Variable
            API_KEY = Variable.get("KENPOM_API_KEY", default_var=None)
        except (ImportError, Exception):
            # Not running in Airflow or Variable doesn't exist
            pass
    
    if not API_KEY:
        raise ValueError(
            "KENPOM_API_KEY not found. Please set it as:\n"
            "1. Environment variable: KENPOM_API_KEY\n"
            "2. Airflow Variable: Admin → Variables → Add 'KENPOM_API_KEY'\n"
            "3. Or in .env file (for local development)"
        )
    
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    
    logger.info(f"Fetching KenPom data for year {year}")
    response = requests.get(
        f"{BASE_URL}?endpoint=ratings&y={year}",
        headers=headers
    )
    response.raise_for_status()
    
    data = response.json()
    df = pd.DataFrame(data)
    logger.info(f"Fetched {len(df)} teams")
    
    return df


def point_in_polygon(point, polygon):
    """
    Check if a point is inside a polygon
    
    Args:
        point: Tuple of (x, y) coordinates
        polygon: Array of polygon vertices
    
    Returns:
        Boolean indicating if point is inside polygon
    """
    path = MPLPath(polygon)
    return path.contains_point(point)


def create_plot(df, output_path='kenpom_ratings_plot.html', year=None):
    """
    Create Plotly visualization of KenPom team ratings
    
    Args:
        df: DataFrame with team ratings data
        output_path: Path to save the HTML plot
        year: Season year (optional, defaults to current year)
    
    Returns:
        Path to saved plot file
    """
    from datetime import datetime
    
    # Get date string for title
    if year:
        date_str = f"{year}-{year+1} Season"
    else:
        date_str = datetime.now().strftime('%B %d, %Y')
    # Define trapezoid points: (64.5,20), (70.2,20), (62.5,40), (72,40)
    trapezoid_points = np.array([
        [64.5, 20],  # bottom left
        [70.2, 20],  # bottom right
        [72, 40],    # top right
        [62.5, 40]   # top left
    ])
    
    # Separate teams inside and outside the trapezoid
    inside_trapezoid = []
    outside_trapezoid = []
    inside_data = []
    outside_data = []
    
    for idx, row in df.iterrows():
        point = (row['AdjTempo'], row['AdjEM'])
        if point_in_polygon(point, trapezoid_points):
            inside_trapezoid.append(idx)
            inside_data.append({
                'x': row['AdjTempo'],
                'y': row['AdjEM'],
                'name': row['TeamName']
            })
        else:
            outside_trapezoid.append(idx)
            outside_data.append({
                'x': row['AdjTempo'],
                'y': row['AdjEM'],
                'name': row['TeamName']
            })
    
    # Create the plotly figure
    fig = go.Figure()
    
    # Add trapezoid shape
    trapezoid_x = [64.5, 70.2, 72, 62.5, 64.5]  # Close the polygon
    trapezoid_y = [20, 20, 40, 40, 20]
    
    fig.add_trace(go.Scatter(
        x=trapezoid_x,
        y=trapezoid_y,
        fill='toself',
        fillcolor='rgba(0,0,0,0.1)',
        line=dict(color='black', width=3),
        mode='lines',
        name='Highlighted Zone (Trapezoid)',
        showlegend=True,
        hoverinfo='skip'
    ))
    
    # Add points outside the trapezoid (blue dots)
    if outside_data:
        fig.add_trace(go.Scatter(
            x=[d['x'] for d in outside_data],
            y=[d['y'] for d in outside_data],
            mode='markers',
            marker=dict(
                size=6,
                color='blue',
                symbol='circle',
                opacity=0.6,
                line=dict(width=0.5, color='#009CDE')
            ),
            text=[d['name'] for d in outside_data],
            hovertemplate='<b>%{text}</b><br>' +
                          'Tempo: %{x:.1f}<br>' +
                          'AdjEM: %{y:.1f}<extra></extra>',
            name='Outside Trapezoid',
            showlegend=True
        ))
    
    # Add points inside the trapezoid (yellow stars)
    if inside_data:
        fig.add_trace(go.Scatter(
            x=[d['x'] for d in inside_data],
            y=[d['y'] for d in inside_data],
            mode='markers',
            marker=dict(
                size=10,
                color='gold',
                symbol='star',
                opacity=0.9,
                line=dict(width=1, color='orange')
            ),
            text=[d['name'] for d in inside_data],
            hovertemplate='<b>%{text}</b><br>' +
                          'Tempo: %{x:.1f}<br>' +
                          'AdjEM: %{y:.1f}<extra></extra>',
            name='Inside Trapezoid',
            showlegend=True
        ))
    
    # Update layout with white theme
    fig.update_layout(
        title=dict(
            text=f'ROAD TO INDIANAPOLIS\n' \
            f'Trapezoid of Excellence\n' \
            f'{date_str}',
            font=dict(size=20, color='#009CDE', family='Arial Black'),
            x=0.5
        ),
        xaxis=dict(
            title=dict(
                text='Adjusted Tempo',
                font=dict(size=16, color='black', family='Arial Black')
            ),
            tickfont=dict(size=12, color='black'),
            gridcolor='rgba(0,0,0,0.1)',
            gridwidth=1,
            showgrid=True,
            zeroline=False
        ),
        yaxis=dict(
            title=dict(
                text='Adjusted Efficiency Margin',
                font=dict(size=16, color='black', family='Arial Black')
            ),
            tickfont=dict(size=12, color='black'),
            gridcolor='rgba(0,0,0,0.1)',
            gridwidth=1,
            showgrid=True,
            zeroline=False
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        width=1200,
        height=800,
        legend=dict(
            x=1.02,
            y=1,
            bgcolor='white',
            bordercolor='black',
            borderwidth=2,
            font=dict(size=12, color='black', family='Arial')
        ),
        hovermode='closest'
    )
    
    # Get the directory of output_path for the PNG file
    output_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else '.'
    png_path = os.path.join(output_dir, 'kenpom_ratings.png')
    
    # Save the HTML plot
    fig.write_html(output_path)
    logger.info(f"Plot saved to {output_path}")
    
    # Try to save PNG (requires Chrome/Chromium to be installed)
    try:
        pio.write_image(fig, png_path, width=1200, height=800)
        logger.info(f"PNG saved to {png_path}")
    except Exception as e:
        logger.warning(f"Could not save PNG image: {str(e)}")
        logger.info("HTML plot was saved successfully. PNG export requires Chrome/Chromium to be installed.")
    
    # Log summary
    logger.info(f"Teams inside the trapezoid: {len(inside_trapezoid)}")
    if inside_trapezoid:
        logger.info("Highlighted Teams:")
        for idx in inside_trapezoid:
            logger.info(f"  - {df.loc[idx, 'TeamName']} (Tempo: {df.loc[idx, 'AdjTempo']:.1f}, AdjEM: {df.loc[idx, 'AdjEM']:.1f})")
    
    return output_path


def main(year=None, output_dir='output'):
    """
    Main function to fetch data and create visualization
    
    Args:
        year: Season year
        output_dir: Directory to save output files
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(output_dir, f'kenpom_ratings.html')
        
        # Fetch data
        df = fetch_kenpom_data(year)
        
        # Create plot
        create_plot(df, output_path, year=year)
        
        logger.info("Script completed successfully")
        return output_path
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()