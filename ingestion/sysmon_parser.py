import json


def infer_technique(event):
    event_id = event.get("EventID")

    image = str(event.get("Image", "")).lower()
    command = str(event.get("CommandLine", "")).lower()
    parent = str(event.get("ParentImage", "")).lower()

    # ----------------------------
    # Process Creation (Event ID 1)
    # ----------------------------
    if event_id == 1:

        # Encoded PowerShell
        if "powershell" in image and "-enc" in command:
            return "T1059"

        # Office spawning PowerShell
        if "winword" in parent and "powershell" in image:
            return "T1059"

        # Mimikatz execution
        if "mimikatz" in command:
            return "T1003"

    # ----------------------------
    # Registry Persistence (Event ID 13)
    # ----------------------------
    if event_id == 13:
        return "T1547"

    # ----------------------------
    # Network Connection (Event ID 3)
    # ----------------------------
    if event_id == 3:
        return "T1041"

    return None


def parse_sysmon_log(file_path):
    parsed_events = []

    with open(file_path, "r") as f:
        data = json.load(f)

    for event in data:
        technique_id = infer_technique(event)

        if technique_id:
            parsed_events.append({
                "technique_id": technique_id,
                "host": event.get("Computer", "UNKNOWN_HOST"),
                "timestamp": event.get("UtcTime", "UNKNOWN_TIME")
            })

    return parsed_events