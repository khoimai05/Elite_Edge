FROM quay.io/astronomer/astro-runtime:10.8.0

# The astro-runtime base image automatically handles:
# - System packages from packages.txt (via ONBUILD)
# - Python packages from requirements.txt (via ONBUILD)
#
# System dependencies for plotly/kaleido (libgl1-mesa-glx, libglib2.0-0)
# are listed in packages.txt
#
# Note: PNG export requires Chrome/Chromium, but HTML export works without it.
# The script will generate HTML successfully and skip PNG if Chrome is not available.

