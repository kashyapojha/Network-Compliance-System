"""Helpers for device trust scoring and display."""


def compute_trust_score(device, fingerprinting_service=None):
    """Compute trust score from device state (authorization, certs, profile)."""
    if device.is_quarantined:
        return 10.0

    score = 100.0
    if fingerprinting_service:
        score = fingerprinting_service.calculate_trust_score(device)
    else:
        if getattr(device, 'vendor', None) == 'Unknown':
            score -= 20
        if getattr(device, 'os_fingerprint', None) in (None, 'Unknown'):
            score -= 15

    if not device.is_authorized:
        score = min(score, 45.0)
    elif device.certificates:
        active = [c for c in device.certificates if not c.is_revoked]
        if active:
            score = max(score, 85.0)

    return round(max(0.0, min(100.0, score)), 1)
