# ./pulumi/core/metadata.py
# Description:
# TODO: enhance with support for propagation of labels annotations on AWS resources
# TODO: enhance by adding additional data to global tags / labels / annotation metadata
#       - git release tag

import subprocess
import pulumi
import threading
from typing import Dict

class MetadataSingleton:
    _instance = None
    __lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls.__lock:
                if not cls._instance:
                    cls._instance = super(MetadataSingleton, cls).__new__(cls)
                    cls._instance._data = {"_global_labels": {}, "_global_annotations": {}}
        return cls._instance

def set_global_labels(labels: Dict[str, str]):
    MetadataSingleton()._data["_global_labels"] = labels

def set_global_annotations(annotations: Dict[str, str]):
    MetadataSingleton()._data["_global_annotations"] = annotations

def get_global_labels() -> Dict[str, str]:
    return MetadataSingleton()._data["_global_labels"]

def get_global_annotations() -> Dict[str, str]:
    return MetadataSingleton()._data["_global_annotations"]

def collect_git_info() -> Dict[str, str]:
    try:
        remote = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url'], stderr=subprocess.STDOUT).strip().decode('utf-8')
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stderr=subprocess.STDOUT).strip().decode('utf-8')
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], stderr=subprocess.STDOUT).strip().decode('utf-8')
        return {'remote': remote, 'branch': branch, 'commit': commit}
    except subprocess.CalledProcessError as e:
        pulumi.log.error(f"Error fetching git information: {e}")
        return {'remote': 'N/A', 'branch': 'N/A', 'commit': 'N/A'}

def generate_git_labels(git_info: Dict[str, str]) -> Dict[str, str]:
    return {
        "git.branch": git_info.get("branch", ""),
        "git.commit": git_info.get("commit", "")[:7],
    }

def generate_git_annotations(git_info: Dict[str, str]) -> Dict[str, str]:
    return {
        "git.remote": git_info.get("remote", ""),
        "git.commit.full": git_info.get("commit", ""),
        "git.branch": git_info.get("branch", "")
    }
