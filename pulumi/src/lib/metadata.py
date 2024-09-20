# src/lib/metadata.py

import subprocess
from typing import Dict
from .utils import sanitize_label_value, extract_repo_name

def collect_git_info() -> Dict[str, str]:
    """
    Retrieves the current Git repository's remote URL, branch, and commit hash.

    This function uses subprocess to run git commands that fetch the remote URL, the current branch,
    and the latest commit hash. This information is useful for tracking which version of the code
    is being deployed, which branch it’s from, and which repository it originates from.

    Returns:
        Dict[str, str]: A dictionary containing the remote URL, branch name, and commit hash.
    """
    try:
        # Fetch the remote URL from git configuration
        remote = subprocess.check_output(
            ['git', 'config', '--get', 'remote.origin.url'],
            stderr=subprocess.STDOUT
        ).strip().decode('utf-8')

        # Fetch the current branch name
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.STDOUT
        ).strip().decode('utf-8')

        # Fetch the latest commit hash
        commit = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            stderr=subprocess.STDOUT
        ).strip().decode('utf-8')

        return {'remote': remote, 'branch': branch, 'commit': commit}

    except subprocess.CalledProcessError as e:
        # In case of an error, log it and return 'N/A' for all values
        pulumi.log.error(f"Error fetching git information: {e.output.decode('utf-8')}")
        return {'remote': 'N/A', 'branch': 'N/A', 'commit': 'N/A'}


def generate_git_labels(git_info: Dict[str, str]) -> Dict[str, str]:
    """
    Generates labels for Kubernetes resources from git information.

    Labels are key/value pairs that are attached to objects, such as pods. Labels are intended to be
    used to specify identifying attributes of objects that are meaningful and relevant to users.

    Args:
        git_info (Dict[str, str]): A dictionary containing git information.

    Returns:
        Dict[str, str]: A dictionary containing sanitized git branch name and shortened commit hash.
    """
    return {
        "git.branch": sanitize_label_value(git_info.get("branch", "")),
        "git.commit": git_info.get("commit", "")[:7],  # Shorten commit hash
    }


def generate_git_annotations(git_info: Dict[str, str]) -> Dict[str, str]:
    """
    Generates annotations for Kubernetes resources from git information.

    Annotations are key/value pairs that can hold arbitrary non-identifying metadata. They are
    intended to store information that can be useful for debugging, auditing, or other purposes.

    Args:
        git_info (Dict[str, str]): A dictionary containing git information.

    Returns:
        Dict[str, str]: A dictionary containing git remote URL, full commit hash, and branch name.
    """
    return {
        "git.remote": git_info.get("remote", ""),
        "git.commit.full": git_info.get("commit", ""),
        "git.branch": git_info.get("branch", "")
    }


##########################################
# Global labels and annotations
##########################################

class MetadataSingleton:
    """
    Singleton class to manage global labels and annotations for Kubernetes resources.

    This class uses the singleton pattern to ensure only one instance is created.
    This is important for global state management.
    """

    __instance = None

    def __new__(cls):
        """
        Ensure only one instance of this class exists (Singleton pattern).

        This method checks if an instance already exists. If not, it creates one.
        """
        if cls.__instance is None:
            cls.__instance = super(MetadataSingleton, cls).__new__(cls)
            cls.__instance._global_labels = {}
            cls.__instance._global_annotations = {}
        return cls.__instance

    @property
    def global_labels(self):
        """
        Property method to get global labels.

        Labels are useful for identifying and grouping Kubernetes resources.
        """
        return self._global_labels

    @global_labels.setter
    def global_labels(self, labels):
        """
        Property method to set global labels.

        Args:
            labels (dict): A dictionary of labels to set globally.
        """
        self._global_labels = labels

    @property
    def global_annotations(self):
        """
        Property method to get global annotations.

        Annotations provide additional context and useful metadata for Kubernetes resources.
        """
        return self._global_annotations

    @global_annotations.setter
    def global_annotations(self, annotations):
        """
        Property method to set global annotations.

        Args:
            annotations (dict): A dictionary of annotations to set globally.
        """
        self._global_annotations = annotations


# Singleton instance for managing global labels and annotations
_metadata_singleton = MetadataSingleton()


def set_global_labels(labels: Dict[str, str]):
    """
    Function to set global labels using the singleton instance.

    Args:
        labels (Dict[str, str]): A dictionary of labels to set globally.
    """
    _metadata_singleton.global_labels = labels


def set_global_annotations(annotations: Dict[str, str]):
    """
    Function to set global annotations using the singleton instance.

    Args:
        annotations (Dict[str, str]): A dictionary of annotations to set globally.
    """
    _metadata_singleton.global_annotations = annotations


def get_global_labels() -> Dict[str, str]:
    """
    Function to get global labels from the singleton instance.

    Returns:
        Dict[str, str]: A dictionary of global labels.
    """
    return _metadata_singleton.global_labels


def get_global_annotations() -> Dict[str, str]:
    """
    Function to get global annotations from the singleton instance.

    Returns:
        Dict[str, str]: A dictionary of global annotations.
    """
    return _metadata_singleton.global_annotations
