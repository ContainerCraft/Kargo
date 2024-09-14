# src/lib/versions.py

import json
import os
import pulumi
import requests

def load_default_versions(config: pulumi.Config) -> dict:
    # Get stack name
    stack_name = pulumi.get_stack()

    # Get configuration settings
    default_versions_source = config.get('default_versions.source')
    versions_channel = config.get('versions.channel') or 'stable'
    versions_stack_name = config.get_bool('versions.stack_name') or False

    default_versions = {}

    def load_versions_from_file(file_path):
        try:
            with open(file_path, 'r') as f:
                versions = json.load(f)
                pulumi.log.info(f"Loaded default versions from file: {file_path}")
                return versions
        except FileNotFoundError:
            pulumi.log.warn(f"Default versions file not found at {file_path}.")
        except json.JSONDecodeError as e:
            pulumi.log.error(f"Error decoding JSON from {file_path}: {e}")
        return None

    def load_versions_from_url(url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            versions = response.json()
            pulumi.log.info(f"Loaded default versions from URL: {url}")
            return versions
        except requests.RequestException as e:
            pulumi.log.warn(f"Failed to fetch default versions from {url}: {e}")
        except json.JSONDecodeError as e:
            pulumi.log.error(f"Error decoding JSON from {url}: {e}")
        return None

    # Determine the precedence of version sources
    if default_versions_source:
        # User-specified source via Pulumi config
        if default_versions_source.startswith(('http://', 'https://')):
            # It's a URL
            default_versions = load_versions_from_url(default_versions_source)
        else:
            # It's a file path
            default_versions = load_versions_from_file(default_versions_source)

        if not default_versions:
            pulumi.log.error(f"Failed to load default versions from specified source: {default_versions_source}")
            raise Exception("Cannot proceed without default versions.")

    else:
        # Check if versions.stack_name is set to true
        if versions_stack_name:
            # Attempt to load versions from ./versions/$STACK_NAME.json
            current_dir = os.path.dirname(os.path.abspath(__file__))
            versions_dir = os.path.join(current_dir, '..', '..', 'versions')
            stack_versions_path = os.path.join(versions_dir, f'{stack_name}.json')
            default_versions = load_versions_from_file(stack_versions_path)

        # If versions are still not loaded, attempt to load from local default_versions.json
        if not default_versions:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            default_versions_path = os.path.join(current_dir, '..', '..', 'default_versions.json')
            default_versions = load_versions_from_file(default_versions_path)

        # If still not loaded, attempt to fetch from remote URL based on channel
        if not default_versions:
            # Construct the URL based on the channel
            base_url = 'https://github.com/containercraft/kargo/releases/latest/download/'
            versions_filename = f'{versions_channel}_versions.json'
            versions_url = f'{base_url}{versions_filename}'
            default_versions = load_versions_from_url(versions_url)

        # If versions are still not loaded, log an error and raise an exception
        if not default_versions:
            pulumi.log.error("Could not load default versions from any source. Cannot proceed.")
            raise Exception("Cannot proceed without default versions.")

    return default_versions
