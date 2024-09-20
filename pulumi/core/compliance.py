# core/compliance.py

import json
from typing import Dict
from .types import ComplianceConfig
from .utils import sanitize_label_value

def generate_compliance_labels(compliance_config: ComplianceConfig) -> Dict[str, str]:
    labels = {}
    # Only essential selection flags should be kept in labels
    if compliance_config.fisma.enabled:
        labels['compliance.fisma.enabled'] = 'true'
    if compliance_config.nist.enabled:
        labels['compliance.nist.enabled'] = 'true'
    if compliance_config.scip.environment:
        labels['compliance.scip.environment'] = sanitize_label_value(compliance_config.scip.environment)
    return labels

def generate_compliance_annotations(compliance_config: ComplianceConfig) -> Dict[str, str]:
    annotations = {}
    # Serialize the more complex metadata into JSON objects or strings
    if compliance_config.fisma.level:
        annotations['compliance.fisma.level'] = compliance_config.fisma.level
    if compliance_config.fisma.ato:
        annotations['compliance.fisma.ato'] = json.dumps(compliance_config.fisma.ato)  # Store as JSON

    if compliance_config.nist.controls:
        annotations['compliance.nist.controls'] = json.dumps(compliance_config.nist.controls)  # Store as JSON array
    if compliance_config.nist.auxiliary:
        annotations['compliance.nist.auxiliary'] = json.dumps(compliance_config.nist.auxiliary)
    if compliance_config.nist.exceptions:
        annotations['compliance.nist.exceptions'] = json.dumps(compliance_config.nist.exceptions)

    return annotations
