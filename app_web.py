"""
Modern Web Interface for Fraud Detection System
Beautiful light blue aesthetic with Flask backend
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from src.live.fetch_ethereum import fetch_ethereum_wallet, compute_features
from src.detection.hybrid_detector import HybridDetector
from src.analysis.context_aware_analyzer import ContextAwareAnalyzer
import torch

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize detector and analyzer
detector = HybridDetector()
analyzer = ContextAwareAnalyzer()

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/test')
def test_page():
    """Serve the test page"""
    with open('test_api_response.html', 'r') as f:
        return f.read()

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyze an Ethereum address
    
    Request JSON:
        {
            "address": "0x..."
        }
    
    Response JSON:
        {
            "address": "0x...",
            "final_score": 70.0,
            "category": "High Risk",
            ...
        }
    """
    print(f"\n[DEBUG] ========== NEW ANALYZE REQUEST ==========")
    print(f"[DEBUG] Request method: {request.method}")
    print(f"[DEBUG] Request headers: {dict(request.headers)}")
    
    try:
        data = request.get_json()
        print(f"[DEBUG] Request data: {data}")
        
        if not data or 'address' not in data:
            return jsonify({
                'error': 'Missing address parameter'
            }), 400
        
        address = data['address'].strip()
        
        # Validate Ethereum address format
        if not address.startswith('0x') or len(address) != 42:
            return jsonify({
                'error': 'Invalid Ethereum address format. Must be 0x + 40 hex characters (42 total).'
            }), 400
        
        # Check if address is valid hex
        try:
            int(address[2:], 16)
        except ValueError:
            return jsonify({
                'error': 'Invalid Ethereum address. Contains non-hexadecimal characters.'
            }), 400
        
        print(f"\n{'='*80}")
        print(f"Analyzing address: {address}")
        print(f"{'='*80}\n")
        
        # Fetch wallet data
        features_dict, is_contract, errors, source_code = fetch_ethereum_wallet(
            address,
            user_id="web_user",
            ip_address=request.remote_addr or "0.0.0.0"
        )
        
        if not features_dict:
            return jsonify({
                'error': 'Unable to fetch address data from Etherscan. Please try again.'
            }), 500
        
        # Get GNN prediction (placeholder if model not loaded)
        try:
            # Try to load GNN model if available
            gnn_score = 15.0  # Default fallback
            # You can add actual GNN prediction here if model exists
        except:
            gnn_score = 15.0
        
        # Run hybrid detection
        final_score, category, explanations = detector.detect(
            address,
            features_dict,
            gnn_score
        )
        
        # Get detailed summary
        summary = detector.get_detection_summary(
            address,
            features_dict,
            gnn_score
        )
        
        # Generate context-aware professional analysis
        try:
            context_analysis = analyzer.analyze_with_context(
                address=address,
                final_score=final_score,
                features=features_dict,
                is_contract=is_contract,
                explanations=explanations
            )
            print(f"\n[DEBUG] Context Analysis Generated Successfully!")
            print(f"[DEBUG] Risk Level: {context_analysis.get('risk_level', 'MISSING')}")
            print(f"[DEBUG] Summary length: {len(context_analysis.get('summary', ''))}")
            print(f"[DEBUG] Summary preview: {context_analysis.get('summary', '')[:100]}...")
        except Exception as e:
            print(f"\n[ERROR] Context analysis failed: {e}")
            import traceback
            traceback.print_exc()
            context_analysis = {
                'risk_level': 'ERROR',
                'summary': f'Error generating analysis: {e}',
                'recommendations': [],
                'verdict': 'Unable to generate analysis'
            }
        
        # Prepare response
        response = {
            'address': address,
            'final_score': float(final_score),
            'category': category,
            'gnn_score': float(summary.get('gnn_score', 0)),
            'gnn_confidence': summary.get('gnn_confidence', 'N/A'),
            'ml_score': 0,  # Will be populated by ML if available
            'ml_confidence': 'N/A',
            'rule_score': float(summary.get('rule_score', 0)),
            'blacklist_score': float(summary.get('blacklist_score', 0)),
            'is_blacklisted': summary.get('is_blacklisted', False),
            'blacklist_reason': summary.get('blacklist_reason', None),
            'explanations': explanations,
            'admin_control_raw': float(summary.get('admin_control_raw', 0)),
            'admin_control_adjusted': float(summary.get('admin_control_adjusted', 0)),
            'is_contract': is_contract,
            
            # Context-aware professional analysis
            'context_analysis': context_analysis,
        }
        
        # Try to get ML score if detector has it
        if hasattr(detector, 'ml_detector') and detector.ml_detector:
            try:
                # Convert features for ML
                ml_features = detector._convert_to_ml_features(features_dict)
                ml_proba, ml_confidence = detector.ml_detector.predict(ml_features)
                response['ml_score'] = float(ml_proba * 100)
                response['ml_confidence'] = ml_confidence
            except Exception as e:
                print(f"ML prediction error: {e}")
        
        print(f"\nResult: {final_score:.1f}/100 ({category})")
        print(f"{'='*80}\n")
        
        print(f"[DEBUG] Response keys before return: {list(response.keys())}")
        print(f"[DEBUG] context_analysis in response: {'context_analysis' in response}")
        if 'context_analysis' in response:
            print(f"[DEBUG] context_analysis type: {type(response['context_analysis'])}")
            print(f"[DEBUG] context_analysis keys: {list(response['context_analysis'].keys()) if isinstance(response['context_analysis'], dict) else 'NOT A DICT'}")
        
        return jsonify(response)
    
    except Exception as e:
        print(f"Error analyzing address: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'error': f'Error analyzing address: {str(e)}'
        }), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Fraud Detection API',
        'version': '2.0'
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("="*80)
    print("🚀 FRAUD DETECTION WEB INTERFACE")
    print("="*80)
    print()
    print(f"🌐 Server starting on http://localhost:{port}")
    print()
    print("Features:")
    print("  ✓ Beautiful light blue aesthetic UI")
    print("  ✓ Real-time address validation")
    print("  ✓ 5-layer detection system")
    print("  ✓ Animated progress rings")
    print("  ✓ Detailed explanations")
    print()
    print("="*80)
    print()
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
