from app import create_app
import os

app, socketio = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    print(f"Starting Certificate-Based Network Compliance System on port {port}")
    print(f"Debug mode: {debug}")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
