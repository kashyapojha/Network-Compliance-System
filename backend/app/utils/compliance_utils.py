"""Shared compliance score calculation used by API and reports."""


def calculate_compliance_score(db, network_unresolved=None):
    """
    Compute compliance score (0-100).

    Changes from original:
    - network_unresolved: if provided, use this count for the alert penalty
      instead of the global unresolved count. This ensures the score shown
      on the Dashboard matches the alerts visible on the Alerts page for the
      current network, rather than being dragged down by old alerts from
      other subnets the backend is no longer connected to.
    - Removed quarantine penalty: quarantining a device is a correct security
      response and should not lower the compliance score. It was penalising
      admins for doing the right thing.
    """
    from ..models.device import Device
    from ..models.alert import Alert

    total_devices = db.query(Device).count()
    global_unresolved = db.query(Alert).filter(Alert.is_resolved == False).count()

    # Use network-scoped count for scoring if provided, else fall back to global
    unresolved_for_score = network_unresolved if network_unresolved is not None else global_unresolved

    if total_devices == 0 and unresolved_for_score == 0:
        return 100.0, global_unresolved

    authorized = db.query(Device).filter(Device.is_authorized == True).count()

    # Base: what fraction of registered devices are authorized?
    base_score = (authorized / total_devices * 100) if total_devices > 0 else 100.0

    # Alert penalty: 5 points per unresolved alert on this network, capped at 50
    alert_penalty = min(unresolved_for_score * 5, 50)

    score = max(base_score - alert_penalty, 0)
    return round(score, 2), global_unresolved