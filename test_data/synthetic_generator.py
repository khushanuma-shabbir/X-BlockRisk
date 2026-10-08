"""
Synthetic Feature Generator
Generates realistic feature dictionaries for all synthetic test cases in MASTER_TEST_CASES.csv
"""

class SyntheticFeatureGenerator:
    """Generate features for synthetic patterns"""
    
    # All synthetic patterns with realistic features
    PATTERNS = {
        # ETHEREUM PATTERNS
        'synthetic_high_activity_legit': {
            'Sent tnx': 5000, 'Received Tnx': 4800,
            'Unique Sent To Addresses': 2000, 'Unique Received From Addresses': 1900,
            'total Ether sent': 50000, 'total ether received': 51000,
            'total ether balance': 5000, 'avg val sent': 10, 'avg val received': 10.6,
            'Time Diff between first and last (Mins)': 10000000,
        },
        'synthetic_low_activity_legit': {
            'Sent tnx': 50, 'Received Tnx': 45,
            'Unique Sent To Addresses': 20, 'Unique Received From Addresses': 18,
            'total Ether sent': 100, 'total ether received': 110,
            'total ether balance': 15, 'avg val sent': 2, 'avg val received': 2.4,
            'Time Diff between first and last (Mins)': 15000000,
        },
        'synthetic_high_activity_fraud': {
            'Sent tnx': 2000, 'Received Tnx': 100,
            'Unique Sent To Addresses': 800, 'Unique Received From Addresses': 30,
            'total Ether sent': 50000, 'total ether received': 5000,
            'total ether balance': 0.01, 'avg val sent': 25, 'avg val received': 50,
            'Time Diff between first and last (Mins)': 1000,
        },
        'synthetic_mixer_pattern': {
            'Sent tnx': 5000, 'Received Tnx': 5000,
            'Unique Sent To Addresses': 2000, 'Unique Received From Addresses': 2000,
            'total Ether sent': 100000, 'total ether received': 100000,
            'total ether balance': 0.1, 'avg val sent': 20, 'avg val received': 20,
            'Time Diff between first and last (Mins)': 100,
        },
        'synthetic_phishing_pattern': {
            'Sent tnx': 10, 'Received Tnx': 500,
            'Unique Sent To Addresses': 2, 'Unique Received From Addresses': 400,
            'total Ether sent': 10000, 'total ether received': 800,
            'total ether balance': 0, 'avg val sent': 1000, 'avg val received': 1.6,
            'Time Diff between first and last (Mins)': 200,
        },
        'synthetic_ponzi_pattern': {
            'Sent tnx': 500, 'Received Tnx': 2000,
            'Unique Sent To Addresses': 100, 'Unique Received From Addresses': 1500,
            'total Ether sent': 50000, 'total ether received': 40000,
            'total ether balance': 0, 'avg val sent': 100, 'avg val received': 20,
            'Time Diff between first and last (Mins)': 5000,
        },
        'synthetic_exchange_pattern': {
            'Sent tnx': 10000, 'Received Tnx': 9800,
            'Unique Sent To Addresses': 5000, 'Unique Received From Addresses': 4900,
            'total Ether sent': 500000, 'total ether received': 510000,
            'total ether balance': 50000, 'avg val sent': 50, 'avg val received': 52,
            'Time Diff between first and last (Mins)': 20000000,
        },
        'synthetic_hodler_pattern': {
            'Sent tnx': 5, 'Received Tnx': 100,
            'Unique Sent To Addresses': 3, 'Unique Received From Addresses': 20,
            'total Ether sent': 10, 'total ether received': 500,
            'total ether balance': 490, 'avg val sent': 2, 'avg val received': 5,
            'Time Diff between first and last (Mins)': 30000000,
        },
        'synthetic_trader_pattern': {
            'Sent tnx': 500, 'Received Tnx': 480,
            'Unique Sent To Addresses': 50, 'Unique Received From Addresses': 48,
            'total Ether sent': 5000, 'total ether received': 5200,
            'total ether balance': 300, 'avg val sent': 10, 'avg val received': 10.8,
            'Time Diff between first and last (Mins)': 10000000,
        },
        'synthetic_contract_pattern': {
            'Sent tnx': 50000, 'Received Tnx': 50000,
            'Unique Sent To Addresses': 10000, 'Unique Received From Addresses': 10000,
            'total Ether sent': 1000000, 'total ether received': 1000000,
            'total ether balance': 10000, 'avg val sent': 20, 'avg val received': 20,
            'Time Diff between first and last (Mins)': 15000000,
        },
        'synthetic_edge_medium_1': {
            'Sent tnx': 100, 'Received Tnx': 80,
            'Unique Sent To Addresses': 60, 'Unique Received From Addresses': 20,
            'total Ether sent': 1000, 'total ether received': 800,
            'total ether balance': 50, 'avg val sent': 10, 'avg val received': 10,
            'Time Diff between first and last (Mins)': 500,
        },
        'synthetic_edge_medium_2': {
            'Sent tnx': 200, 'Received Tnx': 180,
            'Unique Sent To Addresses': 100, 'Unique Received From Addresses': 90,
            'total Ether sent': 2000, 'total ether received': 2100,
            'total ether balance': 150, 'avg val sent': 10, 'avg val received': 11.7,
            'Time Diff between first and last (Mins)': 10000000,
        },
        'synthetic_new_wallet_legit': {
            'Sent tnx': 5, 'Received Tnx': 3,
            'Unique Sent To Addresses': 3, 'Unique Received From Addresses': 2,
            'total Ether sent': 5, 'total ether received': 10,
            'total ether balance': 5, 'avg val sent': 1, 'avg val received': 3.3,
            'Time Diff between first and last (Mins)': 1000,
        },
        'synthetic_new_wallet_suspicious': {
            'Sent tnx': 10, 'Received Tnx': 5,
            'Unique Sent To Addresses': 8, 'Unique Received From Addresses': 2,
            'total Ether sent': 100, 'total ether received': 50,
            'total ether balance': 0, 'avg val sent': 10, 'avg val received': 10,
            'Time Diff between first and last (Mins)': 60,
        },
        'synthetic_dormant_reactivated': {
            'Sent tnx': 50, 'Received Tnx': 45,
            'Unique Sent To Addresses': 20, 'Unique Received From Addresses': 18,
            'total Ether sent': 100, 'total ether received': 110,
            'total ether balance': 20, 'avg val sent': 2, 'avg val received': 2.4,
            'Time Diff between first and last (Mins)': 50000000,
        },
        'synthetic_airdrop_farmer': {
            'Sent tnx': 10, 'Received Tnx': 500,
            'Unique Sent To Addresses': 5, 'Unique Received From Addresses': 200,
            'total Ether sent': 5, 'total ether received': 100,
            'total ether balance': 95, 'avg val sent': 0.5, 'avg val received': 0.2,
            'Time Diff between first and last (Mins)': 5000000,
        },
        'synthetic_nft_trader': {
            'Sent tnx': 200, 'Received Tnx': 180,
            'Unique Sent To Addresses': 80, 'Unique Received From Addresses': 75,
            'total Ether sent': 500, 'total ether received': 520,
            'total ether balance': 50, 'avg val sent': 2.5, 'avg val received': 2.9,
            'Time Diff between first and last (Mins)': 8000000,
        },
        'synthetic_defi_user': {
            'Sent tnx': 1000, 'Received Tnx': 980,
            'Unique Sent To Addresses': 50, 'Unique Received From Addresses': 48,
            'total Ether sent': 10000, 'total ether received': 10500,
            'total ether balance': 1000, 'avg val sent': 10, 'avg val received': 10.7,
            'Time Diff between first and last (Mins)': 12000000,
        },
        'synthetic_bot_trader': {
            'Sent tnx': 5000, 'Received Tnx': 4900,
            'Unique Sent To Addresses': 100, 'Unique Received From Addresses': 95,
            'total Ether sent': 50000, 'total ether received': 51000,
            'total ether balance': 2000, 'avg val sent': 10, 'avg val received': 10.4,
            'Time Diff between first and last (Mins)': 15000000,
        },
        'synthetic_high_volume_fraud': {
            'Sent tnx': 10000, 'Received Tnx': 500,
            'Unique Sent To Addresses': 5000, 'Unique Received From Addresses': 100,
            'total Ether sent': 500000, 'total ether received': 50000,
            'total ether balance': 0.01, 'avg val sent': 50, 'avg val received': 100,
            'Time Diff between first and last (Mins)': 2000,
        },
        'synthetic_scam_token_creator': {
            'Sent tnx': 1000, 'Received Tnx': 5000,
            'Unique Sent To Addresses': 500, 'Unique Received From Addresses': 2000,
            'total Ether sent': 100000, 'total ether received': 50000,
            'total ether balance': 0, 'avg val sent': 100, 'avg val received': 10,
            'Time Diff between first and last (Mins)': 10000,
        },
        'synthetic_rug_pull_eth': {
            'Sent tnx': 10, 'Received Tnx': 1000,
            'Unique Sent To Addresses': 3, 'Unique Received From Addresses': 500,
            'total Ether sent': 50000, 'total ether received': 50000,
            'total ether balance': 0, 'avg val sent': 5000, 'avg val received': 50,
            'Time Diff between first and last (Mins)': 1000,
        },
        'synthetic_wash_trading': {
            'Sent tnx': 1000, 'Received Tnx': 1000,
            'Unique Sent To Addresses': 10, 'Unique Received From Addresses': 10,
            'total Ether sent': 100000, 'total ether received': 100000,
            'total ether balance': 100, 'avg val sent': 100, 'avg val received': 100,
            'Time Diff between first and last (Mins)': 5000,
        },
        'synthetic_sybil_attack': {
            'Sent tnx': 500, 'Received Tnx': 500,
            'Unique Sent To Addresses': 100, 'Unique Received From Addresses': 100,
            'total Ether sent': 5000, 'total ether received': 5000,
            'total ether balance': 50, 'avg val sent': 10, 'avg val received': 10,
            'Time Diff between first and last (Mins)': 10000,
        },
        'synthetic_legitimate_dao': {
            'Sent tnx': 100, 'Received Tnx': 150,
            'Unique Sent To Addresses': 50, 'Unique Received From Addresses': 80,
            'total Ether sent': 50000, 'total ether received': 60000,
            'total ether balance': 15000, 'avg val sent': 500, 'avg val received': 400,
            'Time Diff between first and last (Mins)': 20000000,
        },
        'synthetic_flash_loan_attacker': {
            'Sent tnx': 10, 'Received Tnx': 10,
            'Unique Sent To Addresses': 5, 'Unique Received From Addresses': 5,
            'total Ether sent': 1000000, 'total ether received': 1100000,
            'total ether balance': 100000, 'avg val sent': 100000, 'avg val received': 110000,
            'Time Diff between first and last (Mins)': 5,
        },
        'synthetic_sandwich_bot': {
            'Sent tnx': 10000, 'Received Tnx': 10000,
            'Unique Sent To Addresses': 100, 'Unique Received From Addresses': 100,
            'total Ether sent': 500000, 'total ether received': 520000,
            'total ether balance': 30000, 'avg val sent': 50, 'avg val received': 52,
            'Time Diff between first and last (Mins)': 10000000,
        },
        'synthetic_arbitrage_bot': {
            'Sent tnx': 5000, 'Received Tnx': 5000,
            'Unique Sent To Addresses': 50, 'Unique Received From Addresses': 50,
            'total Ether sent': 200000, 'total ether received': 210000,
            'total ether balance': 15000, 'avg val sent': 40, 'avg val received': 42,
            'Time Diff between first and last (Mins)': 15000000,
        },
        'synthetic_liquidation_bot': {
            'Sent tnx': 2000, 'Received Tnx': 2000,
            'Unique Sent To Addresses': 100, 'Unique Received From Addresses': 100,
            'total Ether sent': 100000, 'total ether received': 105000,
            'total ether balance': 10000, 'avg val sent': 50, 'avg val received': 52.5,
            'Time Diff between first and last (Mins)': 12000000,
        },
        'synthetic_scam_airdrop': {
            'Sent tnx': 5000, 'Received Tnx': 100,
            'Unique Sent To Addresses': 3000, 'Unique Received From Addresses': 20,
            'total Ether sent': 10, 'total ether received': 500,
            'total ether balance': 0, 'avg val sent': 0.002, 'avg val received': 5,
            'Time Diff between first and last (Mins)': 1000,
        },
        'synthetic_dusting_attack': {
            'Sent tnx': 10000, 'Received Tnx': 10,
            'Unique Sent To Addresses': 8000, 'Unique Received From Addresses': 5,
            'total Ether sent': 1, 'total ether received': 10,
            'total ether balance': 9, 'avg val sent': 0.0001, 'avg val received': 1,
            'Time Diff between first and last (Mins)': 100,
        },
        'synthetic_address_poisoning': {
            'Sent tnx': 1000, 'Received Tnx': 50,
            'Unique Sent To Addresses': 800, 'Unique Received From Addresses': 10,
            'total Ether sent': 1, 'total ether received': 100,
            'total ether balance': 99, 'avg val sent': 0.001, 'avg val received': 2,
            'Time Diff between first and last (Mins)': 5000,
        },
        'synthetic_ice_phishing': {
            'Sent tnx': 500, 'Received Tnx': 500,
            'Unique Sent To Addresses': 200, 'Unique Received From Addresses': 300,
            'total Ether sent': 50000, 'total ether received': 1000,
            'total ether balance': 0, 'avg val sent': 100, 'avg val received': 2,
            'Time Diff between first and last (Mins)': 2000,
        },
        'synthetic_rugpull_token': {
            'Sent tnx': 50, 'Received Tnx': 2000,
            'Unique Sent To Addresses': 10, 'Unique Received From Addresses': 1500,
            'total Ether sent': 100000, 'total ether received': 100000,
            'total ether balance': 0, 'avg val sent': 2000, 'avg val received': 50,
            'Time Diff between first and last (Mins)': 500,
        },
        'synthetic_pyramid_scheme': {
            'Sent tnx': 1000, 'Received Tnx': 5000,
            'Unique Sent To Addresses': 500, 'Unique Received From Addresses': 3000,
            'total Ether sent': 100000, 'total ether received': 50000,
            'total ether balance': 0, 'avg val sent': 100, 'avg val received': 10,
            'Time Diff between first and last (Mins)': 10000,
        },
        'synthetic_lending_protocol': {
            'Sent tnx': 500, 'Received Tnx': 480,
            'Unique Sent To Addresses': 20, 'Unique Received From Addresses': 18,
            'total Ether sent': 10000, 'total ether received': 10500,
            'total ether balance': 1000, 'avg val sent': 20, 'avg val received': 21.9,
            'Time Diff between first and last (Mins)': 10000000,
        },
        'synthetic_yield_farmer': {
            'Sent tnx': 200, 'Received Tnx': 180,
            'Unique Sent To Addresses': 30, 'Unique Received From Addresses': 28,
            'total Ether sent': 5000, 'total ether received': 5500,
            'total ether balance': 1000, 'avg val sent': 25, 'avg val received': 30.6,
            'Time Diff between first and last (Mins)': 8000000,
        },
        'synthetic_liquidity_provider': {
            'Sent tnx': 100, 'Received Tnx': 90,
            'Unique Sent To Addresses': 10, 'Unique Received From Addresses': 8,
            'total Ether sent': 10000, 'total ether received': 11000,
            'total ether balance': 2000, 'avg val sent': 100, 'avg val received': 122.2,
            'Time Diff between first and last (Mins)': 12000000,
        },
        'synthetic_staker': {
            'Sent tnx': 20, 'Received Tnx': 50,
            'Unique Sent To Addresses': 5, 'Unique Received From Addresses': 3,
            'total Ether sent': 1000, 'total ether received': 1100,
            'total ether balance': 1100, 'avg val sent': 50, 'avg val received': 22,
            'Time Diff between first and last (Mins)': 20000000,
        },
        'synthetic_governance_voter': {
            'Sent tnx': 50, 'Received Tnx': 60,
            'Unique Sent To Addresses': 10, 'Unique Received From Addresses': 8,
            'total Ether sent': 100, 'total ether received': 150,
            'total ether balance': 100, 'avg val sent': 2, 'avg val received': 2.5,
            'Time Diff between first and last (Mins)': 15000000,
        },
        'synthetic_multisig_treasury': {
            'Sent tnx': 100, 'Received Tnx': 200,
            'Unique Sent To Addresses': 50, 'Unique Received From Addresses': 100,
            'total Ether sent': 50000, 'total ether received': 60000,
            'total ether balance': 20000, 'avg val sent': 500, 'avg val received': 300,
            'Time Diff between first and last (Mins)': 25000000,
        },
        'synthetic_gnosis_safe': {
            'Sent tnx': 200, 'Received Tnx': 180,
            'Unique Sent To Addresses': 80, 'Unique Received From Addresses': 70,
            'total Ether sent': 10000, 'total ether received': 12000,
            'total ether balance': 5000, 'avg val sent': 50, 'avg val received': 66.7,
            'Time Diff between first and last (Mins)': 18000000,
        },
        'synthetic_escrow_service': {
            'Sent tnx': 500, 'Received Tnx': 500,
            'Unique Sent To Addresses': 200, 'Unique Received From Addresses': 200,
            'total Ether sent': 50000, 'total ether received': 50000,
            'total ether balance': 1000, 'avg val sent': 100, 'avg val received': 100,
            'Time Diff between first and last (Mins)': 15000000,
        },
        'synthetic_payment_processor': {
            'Sent tnx': 10000, 'Received Tnx': 10000,
            'Unique Sent To Addresses': 5000, 'Unique Received From Addresses': 5000,
            'total Ether sent': 500000, 'total ether received': 500000,
            'total ether balance': 10000, 'avg val sent': 50, 'avg val received': 50,
            'Time Diff between first and last (Mins)': 20000000,
        },
        'synthetic_donation_address': {
            'Sent tnx': 50, 'Received Tnx': 500,
            'Unique Sent To Addresses': 20, 'Unique Received From Addresses': 400,
            'total Ether sent': 10000, 'total ether received': 10000,
            'total ether balance': 500, 'avg val sent': 200, 'avg val received': 20,
            'Time Diff between first and last (Mins)': 15000000,
        },
        'synthetic_bridge_user': {
            'Sent tnx': 100, 'Received Tnx': 90,
            'Unique Sent To Addresses': 20, 'Unique Received From Addresses': 18,
            'total Ether sent': 5000, 'total ether received': 5000,
            'total ether balance': 500, 'avg val sent': 50, 'avg val received': 55.6,
            'Time Diff between first and last (Mins)': 10000000,
        },
        'synthetic_rollup_user': {
            'Sent tnx': 500, 'Received Tnx': 480,
            'Unique Sent To Addresses': 50, 'Unique Received From Addresses': 48,
            'total Ether sent': 2000, 'total ether received': 2100,
            'total ether balance': 500, 'avg val sent': 4, 'avg val received': 4.4,
            'Time Diff between first and last (Mins)': 12000000,
        },
        'synthetic_smart_wallet': {
            'Sent tnx': 200, 'Received Tnx': 180,
            'Unique Sent To Addresses': 80, 'Unique Received From Addresses': 75,
            'total Ether sent': 1000, 'total ether received': 1100,
            'total ether balance': 200, 'avg val sent': 5, 'avg val received': 6.1,
            'Time Diff between first and last (Mins)': 8000000,
        },
        'synthetic_social_recovery': {
            'Sent tnx': 100, 'Received Tnx': 90,
            'Unique Sent To Addresses': 40, 'Unique Received From Addresses': 35,
            'total Ether sent': 500, 'total ether received': 550,
            'total ether balance': 100, 'avg val sent': 5, 'avg val received': 6.1,
            'Time Diff between first and last (Mins)': 10000000,
        },
        'synthetic_gasless_tx': {
            'Sent tnx': 300, 'Received Tnx': 280,
            'Unique Sent To Addresses': 100, 'Unique Received From Addresses': 95,
            'total Ether sent': 1500, 'total ether received': 1600,
            'total ether balance': 300, 'avg val sent': 5, 'avg val received': 5.7,
            'Time Diff between first and last (Mins)': 9000000,
        },
        'synthetic_tornado_cash_user': {
            'Sent tnx': 50, 'Received Tnx': 50,
            'Unique Sent To Addresses': 10, 'Unique Received From Addresses': 10,
            'total Ether sent': 1000, 'total ether received': 1000,
            'total ether balance': 10, 'avg val sent': 20, 'avg val received': 20,
            'Time Diff between first and last (Mins)': 5000000,
        },
        'synthetic_newborn_exchange': {
            'Sent tnx': 1000, 'Received Tnx': 900,
            'Unique Sent To Addresses': 500, 'Unique Received From Addresses': 450,
            'total Ether sent': 50000, 'total ether received': 52000,
            'total ether balance': 5000, 'avg val sent': 50, 'avg val received': 57.8,
            'Time Diff between first and last (Mins)': 100000,
        },
        'synthetic_high_frequency_trader': {
            'Sent tnx': 50000, 'Received Tnx': 50000,
            'Unique Sent To Addresses': 100, 'Unique Received From Addresses': 100,
            'total Ether sent': 1000000, 'total ether received': 1020000,
            'total ether balance': 30000, 'avg val sent': 20, 'avg val received': 20.4,
            'Time Diff between first and last (Mins)': 10000000,
        },
        'synthetic_mixer_legitimate': {
            'Sent tnx': 100, 'Received Tnx': 100,
            'Unique Sent To Addresses': 50, 'Unique Received From Addresses': 50,
            'total Ether sent': 10000, 'total ether received': 10000,
            'total ether balance': 100, 'avg val sent': 100, 'avg val received': 100,
            'Time Diff between first and last (Mins)': 5000000,
        },
        'synthetic_otc_desk': {
            'Sent tnx': 50, 'Received Tnx': 48,
            'Unique Sent To Addresses': 20, 'Unique Received From Addresses': 19,
            'total Ether sent': 500000, 'total ether received': 510000,
            'total ether balance': 20000, 'avg val sent': 10000, 'avg val received': 10625,
            'Time Diff between first and last (Mins)': 15000000,
        },
    }
    
    def generate(self, pattern_name: str) -> dict:
        """Generate features for a synthetic pattern"""
        features = self.PATTERNS.get(pattern_name, {})
        
        # Add default values for missing features
        defaults = {
            'Sent tnx': 0,
            'Received Tnx': 0,
            'Unique Sent To Addresses': 0,
            'Unique Received From Addresses': 0,
            'total Ether sent': 0,
            'total ether received': 0,
            'total ether balance': 0,
            'avg val sent': 0,
            'avg val received': 0,
            'Time Diff between first and last (Mins)': 0,
            # Admin control defaults (for non-contracts)
            'can_mint': 0,
            'has_blacklist': 0,
            'can_pause': 0,
            'fee_too_high': 0,
            'has_trading_limits': 0,
            'has_trading_cooldown': 0,
            'owner_can_withdraw': 0,
            'owner_change_balance': 0,
            # DEX defaults
            'total_liquidity_usd': 0,
            'pair_created_days': 0,
        }
        
        # Merge with defaults
        result = {**defaults, **features}
        return result
    
    def generate_all(self) -> dict:
        """Generate all synthetic patterns"""
        return {name: self.generate(name) for name in self.PATTERNS.keys()}
    
    def list_patterns(self) -> list:
        """List all available patterns"""
        return list(self.PATTERNS.keys())


if __name__ == '__main__':
    gen = SyntheticFeatureGenerator()
    print(f"Total patterns: {len(gen.list_patterns())}")
    
    # Test one pattern
    test_pattern = 'synthetic_phishing_pattern'
    features = gen.generate(test_pattern)
    print(f"\nExample: {test_pattern}")
    for k, v in features.items():
        if v != 0:
            print(f"  {k}: {v}")
