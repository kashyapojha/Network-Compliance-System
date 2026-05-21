from app import create_app
from app.config import Config
from app.services.monitoring_service import MonitoringService
import threading

app, socketio = create_app()

monitoring_service = None
monitoring_thread = None


def start_background_monitoring():
    """Start continuous background network scanning."""
    global monitoring_service, monitoring_thread

    if not Config.AUTO_START_MONITORING:
        print("Background monitoring disabled (AUTO_START_MONITORING=false)")
        return

    if monitoring_service and monitoring_service.is_running:
        return

    monitoring_service = MonitoringService()
    monitoring_thread = threading.Thread(target=monitoring_service.start, daemon=True)
    monitoring_thread.start()
    print(f"Background monitoring started (every {Config.POLL_INTERVAL}s on {monitoring_service.network_range})")


if __name__ == '__main__':
    print(f"Starting Network Compliance System on port {Config.PORT}")
    print(f"Debug mode: {Config.DEBUG}")
    start_background_monitoring()
    socketio.run(app, host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
