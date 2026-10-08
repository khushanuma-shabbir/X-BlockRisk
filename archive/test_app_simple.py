"""
Simplified test app to verify everything works
"""
import streamlit as st
import sys
import os

# Add project to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

st.title("🔍 Fraud Detector - Simple Test")

st.write("Testing if the system works...")

# Test 1: Import test
with st.expander("✅ Test 1: Module Imports"):
    try:
        from src.live.fetch_ethereum import fetch_ethereum_wallet
        st.success("✓ fetch_ethereum_wallet imported successfully")
    except Exception as e:
        st.error(f"✗ Import failed: {e}")

# Test 2: Model test
with st.expander("✅ Test 2: Model Files"):
    model_path = "models/ethereum_clean/gnn_22feat.pt"
    if os.path.exists(model_path):
        st.success(f"✓ Model found: {model_path}")
    else:
        st.error(f"✗ Model not found: {model_path}")

# Test 3: API key test
with st.expander("✅ Test 3: API Configuration"):
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv('ETHERSCAN_API_KEY', '')
    if api_key:
        st.success(f"✓ Etherscan API key found (length: {len(api_key)})")
    else:
        st.warning("⚠ No Etherscan API key found")

# Test 4: Live analysis
st.subheader("Test Address Analysis")

test_address = st.text_input(
    "Enter Ethereum address:",
    value="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
)

if st.button("🚀 Test Analysis"):
    try:
        from src.live.fetch_ethereum import fetch_ethereum_wallet
        
        with st.spinner("Analyzing... (may take 10-30 seconds)"):
            features, is_contract, flags, source = fetch_ethereum_wallet(test_address)
        
        if features:
            st.success("✅ Analysis completed successfully!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Features Extracted", len(features))
            with col2:
                st.metric("Data Source", source)
            with col3:
                st.metric("Is Contract", "Yes" if is_contract else "No")
            
            # Show sample features
            st.subheader("Sample Features:")
            sample_features = dict(list(features.items())[:5])
            for key, value in sample_features.items():
                st.write(f"**{key}:** {value:.4f}" if isinstance(value, float) else f"**{key}:** {value}")
            
            st.balloons()
        else:
            st.error("❌ No features returned")
            if flags:
                for flag in flags:
                    st.warning(f"⚠ {flag}")
    
    except Exception as e:
        st.error(f"❌ Error: {e}")
        import traceback
        st.code(traceback.format_exc())

st.markdown("---")
st.info("💡 If this test works, the main app should work too!")
