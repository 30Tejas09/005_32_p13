import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from config import Config

def create_app(config_class=Config):
    # Location of the built frontend
    dist_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'dist'))

    app = Flask(
        __name__,
        static_folder=dist_folder if os.path.exists(dist_folder) else None,
        static_url_path=''
    )
    app.config.from_object(config_class)

    # Enable Cross-Origin Resource Sharing (CORS)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.dfa_routes import dfa_bp
    from app.routes.report_routes import report_bp
    from app.routes.dispatch_routes import dispatch_bp
    from app.routes.handler_routes import handler_bp
    from app.routes.routing_routes import routing_bp
    from app.routes.analytics_routes import analytics_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dfa_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(dispatch_bp)
    app.register_blueprint(handler_bp)
    app.register_blueprint(routing_bp)
    app.register_blueprint(analytics_bp)

    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "Traffic Signal Fault Dispatcher API",
            "version": "1.0.0"
        }), 200

    # Serve built React SPA
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_react(path):
        if os.path.exists(dist_folder):
            if path != "" and os.path.exists(os.path.join(dist_folder, path)):
                return send_from_directory(dist_folder, path)
            return send_from_directory(dist_folder, 'index.html')
        return jsonify({"message": "Frontend build not found. Run npm run build in frontend/."}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    return app
