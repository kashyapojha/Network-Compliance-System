"""Shared compliance score calculation used by API and reports."""


def calculate_compliance_score(db):
    """
    Compute compliance score (0-100) from device authorization and unresolved alerts.
    """
    from ..models.device import Device
    from ..models.alert import Alert

    total_devices = db.query(Device).count()
    unresolved_alerts = db.query(Alert).filter(Alert.is_resolved == False).count()

    if total_devices == 0 and unresolved_alerts == 0:
        return 100.0, 0

    authorized = db.query(Device).filter(Device.is_authorized == True).count()
    quarantined = db.query(Device).filter(Device.is_quarantined == True).count()

    if total_devices > 0:
        base_score = (authorized / total_devices) * 100
    else:
        base_score = 100.0

    alert_penalty = min(unresolved_alerts * 5, 50)
    quarantine_penalty = min(quarantined * 3, 15)

    score = max(base_score - alert_penalty - quarantine_penalty, 0)
    return round(score, 2), unresolved_alerts
