# src/cert_manager/types.py

"""
Types and data structures specific to the Cert Manager module.

This module defines the configuration data class for the Cert Manager module,
which is used to manage SSL/TLS certificates within the Kubernetes cluster.
It standardizes the configuration options and provides methods to merge user
configurations with default settings.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import pulumi

@dataclass
class CertManagerConfig:
    """
    Configuration for deploying the Cert Manager module.

    Attributes:
        namespace (str): The Kubernetes namespace where cert-manager will be deployed.
            Defaults to "cert-manager".
        version (Optional[str]): The version of the cert-manager Helm chart to deploy.
            If None, the default version from the versions management system will be used.
        cluster_issuer (str): The name of the ClusterIssuer to create for certificate issuance.
            Defaults to "cluster-selfsigned-issuer".
        install_crds (bool): Whether to install Custom Resource Definitions (CRDs) required by cert-manager.
            Defaults to True.
    """
    namespace: str = "cert-manager"
    version: Optional[str] = None
    cluster_issuer: str = "cluster-selfsigned-issuer"
    install_crds: bool = True

    @staticmethod
    def merge(user_config: Dict[str, Any]) -> 'CertManagerConfig':
        """
        Merges user-provided configuration with default values.

        This method creates a new CertManagerConfig instance by combining the
        default configuration with any user-specified settings. It ensures that
        all required fields are set and warns the user about any unknown configuration keys.

        Args:
            user_config (Dict[str, Any]): A dictionary containing user-provided configuration options.

        Returns:
            CertManagerConfig: An instance of CertManagerConfig with merged settings.

        Example:
            ```python
            # User-provided configuration
            user_config = {
                "namespace": "my-cert-manager",
                "install_crds": False
            }

            # Merge with defaults
            config = CertManagerConfig.merge(user_config)
            ```
        """
        # Create a default configuration instance
        default_config = CertManagerConfig()
        # Copy default configuration into a dictionary
        merged_config = default_config.__dict__.copy()
        # Iterate over user-provided configuration and update the merged_config
        for key, value in user_config.items():
            if hasattr(default_config, key):
                # If the key exists in the default configuration, update the value
                merged_config[key] = value
            else:
                # Warn the user about any unknown configuration keys
                pulumi.log.warn(f"Unknown configuration key '{key}' in cert_manager config.")
        # Return a new CertManagerConfig instance with merged settings
        return CertManagerConfig(**merged_config)
