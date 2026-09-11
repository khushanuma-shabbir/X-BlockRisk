"""
Feature column definitions for Ethereum fraud detection
Used by live API to ensure feature consistency
"""

# Ethereum feature columns (38 features matching training data)
ETHEREUM_FEATURE_COLUMNS = [
    'Avg min between sent tnx',
    'Avg min between received tnx',
    'Time Diff between first and last (Mins)',
    'Sent tnx',
    'Received Tnx',
    'Number of Created Contracts',
    'Unique Received From Addresses',
    'Unique Sent To Addresses',
    'min value received',
    'max value received',
    'avg val received',
    'min val sent',
    'max val sent',
    'avg val sent',
    'min value sent to contract',
    'max val sent to contract',
    'avg value sent to contract',
    'total transactions (including tnx to create contract',
    'total Ether sent',
    'total ether received',
    'total ether sent contracts',
    'total ether balance',
    'Total ERC20 tnxs',
    'ERC20 total Ether received',
    'ERC20 total ether sent',
    'ERC20 total Ether sent contract',
    'ERC20 uniq sent addr',
    'ERC20 uniq rec addr',
    'ERC20 uniq sent addr.1',
    'ERC20 uniq rec contract addr',
    'ERC20 min val rec',
    'ERC20 max val rec',
    'ERC20 avg val rec',
    'ERC20 min val sent',
    'ERC20 max val sent',
    'ERC20 avg val sent',
    'ERC20 uniq sent token name',
    'ERC20 uniq rec token name'
]


def validate_feature_dict(features):
    """
    Validate that feature dictionary contains all required columns
    Returns: (is_valid, missing_columns)
    """
    missing = [col for col in ETHEREUM_FEATURE_COLUMNS if col not in features]
    return len(missing) == 0, missing
