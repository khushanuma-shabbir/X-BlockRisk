"""Simple Flask test"""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/test')
def test():
    return jsonify({'status': 'working', 'message': 'Flask is running!'})

if __name__ == '__main__':
    print("Starting simple Flask test server...")
    app.run(host='0.0.0.0', port=5001, debug=False)
