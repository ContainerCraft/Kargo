import base64
import os

def encode_file_to_base64(file_name):
    file_path = os.path.join(os.path.dirname(__file__), "assets", file_name)
    with open(file_path, "rb") as file:
        encoded_string = base64.b64encode(file.read()).decode("utf-8")
    return encoded_string

def return_encoded_assets():
    # Define file names
    kubevirt_png = "kubevirt.png"
    prometheus_png = "prometheus.png"
    alertmanager_png = "alertmanager.png"
    grafana_png = "grafana.png"

    # Encode files to base64
    kubevirt_icon = encode_file_to_base64(kubevirt_png)
    prometheus_icon = encode_file_to_base64(prometheus_png)
    alertmanager_icon = encode_file_to_base64(alertmanager_png)
    grafana_icon = encode_file_to_base64(grafana_png)

    # Create the assets dictionary
    assets = {
        "kubevirt_icon": kubevirt_icon,
        "prometheus_icon": prometheus_icon,
        "alertmanager_icon": alertmanager_icon,
        "grafana_icon": grafana_icon
    }

    return assets
