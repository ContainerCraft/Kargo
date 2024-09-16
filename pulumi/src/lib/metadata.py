# src/lib/metadata.py

import subprocess
from typing import Dict
from .utils import sanitize_label_value, extract_repo_name

def collect_git_info() -> Dict[str, str]:
    """
    Retrieves the current Git repository's remote URL, branch, and commit hash.
    """
    try:
        remote = subprocess.check_output(
            ['git', 'config', '--get', 'remote.origin.url'],
            stderr=subprocess.STDOUT
        ).strip().decode('utf-8')

        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.STDOUT
        ).strip().decode('utf-8')

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

def generate_git_labels(git_info: Dict[str, str]) -> Dict[str, str]:
    # Only essential metadata should be in labels (e.g., branch)
    labels = {
        "git.branch": sanitize_label_value(git_info.get("branch", "")),
        "git.commit": git_info.get("commit", "")[:7],  # Shorten commit hash
    }
    return {k: v for k, v in labels.items() if v}

def generate_git_annotations(git_info: Dict[str, str]) -> Dict[str, str]:
    # Store more detailed information in annotations
    annotations = {
        "git.remote": git_info.get("remote", ""),
        "git.commit.full": git_info.get("commit", ""),
        "git.branch": git_info.get("branch", "")
    }
    return {k: v for k, v in annotations.items() if v}

##########################################
# Global labels and annotations
# Singleton to store global labels and annotations
_global_labels = {}
_global_annotations = {}

def set_global_labels(labels):
    global _global_labels
    _global_labels = labels

def set_global_annotations(annotations):
    global _global_annotations
    _global_annotations = annotations

def get_global_labels():
    return _global_labels

def get_global_annotations():
    return _global_annotations
