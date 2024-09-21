# ./pulumi/core/helm.py
# Description:

import requests
import logging
import yaml
from packaging.version import parse as parse_version, InvalidVersion, Version
from typing import Dict, Any

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HELM_CHART_URL_TEMPLATE = "https://github.com/containercraft/kargo/releases/latest/download/"
CHART_NOT_FOUND = "Chart not found"

def is_stable_version(version_str: str) -> bool:
    try:
        parsed_version = parse_version(version_str)
        return isinstance(parsed_version, Version) and not parsed_version.is_prerelease and not parsed_version.is_devrelease
    except InvalidVersion:
        return False

def get_latest_helm_chart_version(url: str, chart_name: str) -> str:
    try:
        logging.info(f"Fetching URL: {url}")
        response = requests.get(url)
        response.raise_for_status()

        index = yaml.safe_load(response.content)
        if chart_name in index['entries']:
            chart_versions = index['entries'][chart_name]
            stable_versions = [v for v in chart_versions if is_stable_version(v['version'])]
            if not stable_versions:
                logging.info(f"No stable versions found for chart '{chart_name}'.")
                return CHART_NOT_FOUND
            latest_chart = max(stable_versions, key=lambda x: parse_version(x['version']))
            return latest_chart['version']
        else:
            logging.info(f"No chart named '{chart_name}' found in repository.")
            return CHART_NOT_FOUND

    except requests.RequestException as e:
        logging.error(f"Error fetching data: {e}")
        return f"Error fetching data: {e}"
