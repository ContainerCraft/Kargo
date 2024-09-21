# ./pulumi/core/versions.py
import json
import os
import pulumi
import requests
from typing import Dict

#DEFAULT_VERSIONS_URL_TEMPLATE = 'https://github.com/containercraft/kargo/releases/latest/download/'
# TODO: replace with official github releases artifact URLs when released
DEFAULT_VERSIONS_URL_TEMPLATE = 'https://raw.githubusercontent.com/ContainerCraft/Kargo/rerefactor/pulumi/'

def load_default_versions(config: pulumi.Config, force_refresh=False) -> dict:
    """
    Loads the default versions for modules based on the specified configuration settings.

    This function attempts to load version information from multiple sources in order of precedence:
    1. User-specified source via Pulumi config (`default_versions.source`).
    2. Stack-specific versions file (`./versions/$STACK_NAME.json`) if `versions.stack_name` is set to true.
    3. Local default versions file (`./default_versions.json`).
    4. Remote versions based on the specified channel (`versions.channel`).

    Args:
        config: The Pulumi configuration object.

    Returns:
        A dictionary containing the default versions for modules.

    Raises:
        Exception: If default versions cannot be loaded from any source.
    """
    cache_file = '/tmp/default_versions.json'
    if not force_refresh and os.path.exists(cache_file):
        try:
            with open(cache_file) as f:
                return json.load(f)
        except Exception as e:
            pulumi.log.warn(f"Error reading cache file: {e}")

    stack_name = pulumi.get_stack()
    default_versions_source = config.get('default_versions.source')
    versions_channel = config.get('versions.channel') or 'stable'
    versions_stack_name = config.get_bool('versions.stack_name') or False
    default_versions = {}

    def load_versions_from_file(file_path: str) -> dict:
        try:
            with open(file_path, 'r') as f:
                versions = json.load(f)
                pulumi.log.info(f"Loaded default versions from file: {file_path}")
                return versions
        except (FileNotFoundError, json.JSONDecodeError) as e:
            pulumi.log.warn(f"Error loading versions from file {file_path}: {e}")
        return {}

    def load_versions_from_url(url: str) -> dict:
        try:
            response = requests.get(url)
            response.raise_for_status()
            versions = response.json()
            pulumi.log.info(f"Loaded default versions from URL: {url}")
            return versions
        except (requests.RequestException, json.JSONDecodeError) as e:
            pulumi.log.warn(f"Error loading versions from URL {url}: {e}")
        return {}

    if default_versions_source:
        if default_versions_source.startswith(('http://', 'https://')):
            default_versions = load_versions_from_url(default_versions_source)
        else:
            default_versions = load_versions_from_file(default_versions_source)

        if not default_versions:
            raise Exception(f"Failed to load default versions from specified source: {default_versions_source}")

    else:
        if versions_stack_name:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            stack_versions_path = os.path.join(current_dir, '..', 'versions', f'{stack_name}.json')
            default_versions = load_versions_from_file(stack_versions_path)

        if not default_versions:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            default_versions_path = os.path.join(current_dir, '..', 'default_versions.json')
            default_versions = load_versions_from_file(default_versions_path)

        if not default_versions:
            versions_url = f'{DEFAULT_VERSIONS_URL_TEMPLATE}{versions_channel}_versions.json'
            default_versions = load_versions_from_url(versions_url)

        if not default_versions:
            raise Exception("Cannot proceed without default versions.")

    with open(cache_file, 'w') as f:
        json.dump(default_versions, f)

    return default_versions
