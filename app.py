import os
from flask_app import create_app, socketio

# Set debug based on environment
debug_mode = os.environ.get('FLASK_ENV') != 'production'
app = create_app(debug=debug_mode)

if __name__ == "__main__":
	port = int(os.environ.get("PORT", 8080))
	socketio.run(app, host='0.0.0.0', port=port, debug=debug_mode)