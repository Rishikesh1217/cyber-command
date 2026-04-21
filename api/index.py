import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from server import app
except Exception as e:
    from flask import Flask, jsonify
    app = Flask(__name__)

    @app.route('/api/debug', methods=['GET'])
    def debug():
        return jsonify({"import_error": str(e), "type": type(e).__name__})

    @app.route('/api/<path:path>', methods=['GET', 'POST'])
    def catch_all(path):
        return jsonify({"import_error": str(e), "path": path}), 500
