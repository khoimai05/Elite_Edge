"""
Quick test script to verify KenPom plot generation works
Run this before setting up Airflow to ensure everything is configured correctly
"""

from kenpom_plot import main

if __name__ == "__main__":
    print("Testing KenPom plot generation...")
    try:
        output_path = main(year=2025, output_dir='output')
        print(f"\n✓ Success! Plot saved to: {output_path}")
        print("You can now set up Airflow to run this automatically.")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("Please check your .env file and API key configuration.")

