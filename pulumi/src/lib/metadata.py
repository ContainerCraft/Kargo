# src/lib/metadata.py
# Description: This module contains utility functions for retrieving metadata about the current Pulumi project source code repository.

import subprocess
from typing import Dict

def collect_git_info() -> Dict[str, str]:
    """
    Retrieves the current Git repository's remote URL, branch, and commit hash.

    Returns:
        Dict[str, str]: A dictionary containing the 'remote', 'branch', and 'commit' information.
    """
    try:
        # Get the remote URL
        remote = subprocess.check_output(
            ['git', 'config', '--get', 'remote.origin.url'],
            stderr=subprocess.STDOUT
        ).strip().decode('utf-8')

        # Get the current branch
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.STDOUT
        ).strip().decode('utf-8')

        # Get the latest commit hash
        commit = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            stderr=subprocess.STDOUT
        ).strip().decode('utf-8')

        return {
            'remote': remote,
            'branch': branch,
            'commit': commit
        }

    except subprocess.CalledProcessError as e:
        pulumi.log.error(f"Error fetching git information: {e.output.decode('utf-8')}")
        return {
            'remote': 'N/A',
            'branch': 'N/A',
            'commit': 'N/A'
        }
