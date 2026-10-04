"""
User History & Watchlist Module
Tracks user searches, saves favorites, and provides historical analysis.

Production Features:
- Search history with timestamps
- Watchlist for monitoring addresses
- Historical risk score tracking
- Export search history
- Address tagging and notes
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserHistory:
    """
    Manages user search history and watchlist
    """
    
    def __init__(self, storage_path: str = 'data/user_data'):
        """
        Initialize user history manager
        
        Args:
            storage_path: Directory to store user data
        """
        self.storage_path = storage_path
        self.history_file = os.path.join(storage_path, 'search_history.json')
        self.watchlist_file = os.path.join(storage_path, 'watchlist.json')
        
        # Create storage directory
        os.makedirs(storage_path, exist_ok=True)
        
        # Load existing data
        self.history = self._load_json(self.history_file, default=[])
        self.watchlist = self._load_json(self.watchlist_file, default={})
    
    def _load_json(self, filepath: str, default=None):
        """Load JSON file with error handling"""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading {filepath}: {e}")
                return default if default is not None else {}
        return default if default is not None else {}
    
    def _save_json(self, data, filepath: str):
        """Save data to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving {filepath}: {e}")
            return False
    
    def add_search(
        self, 
        address: str, 
        risk_score: float,
        risk_category: str,
        chain: str = 'ethereum',
        user_id: Optional[str] = None
    ) -> bool:
        """
        Add a search to history
        
        Args:
            address: Wallet address analyzed
            risk_score: Risk score (0-100)
            risk_category: Risk category (Low/Medium/High)
            chain: Blockchain network
            user_id: Optional user identifier
        
        Returns:
            bool indicating success
        """
        search_record = {
            'address': address,
            'risk_score': risk_score,
            'risk_category': risk_category,
            'chain': chain,
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id
        }
        
        self.history.append(search_record)
        
        # Keep only last 1000 searches to prevent unlimited growth
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        
        # Save to disk
        success = self._save_json(self.history, self.history_file)
        
        if success:
            logger.info(f"✓ Added search to history: {address[:10]}... (Risk: {risk_score})")
        
        return success
    
    def get_recent_searches(
        self, 
        limit: int = 20, 
        user_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get recent searches
        
        Args:
            limit: Maximum number of results
            user_id: Filter by user ID (optional)
        
        Returns:
            List of search records
        """
        filtered = self.history
        
        # Filter by user if specified
        if user_id:
            filtered = [s for s in filtered if s.get('user_id') == user_id]
        
        # Return most recent
        return list(reversed(filtered[-limit:]))
    
    def search_history(
        self, 
        address: Optional[str] = None,
        min_risk: Optional[float] = None,
        max_risk: Optional[float] = None,
        chain: Optional[str] = None
    ) -> List[Dict]:
        """
        Search history with filters
        
        Args:
            address: Filter by address (partial match)
            min_risk: Minimum risk score
            max_risk: Maximum risk score
            chain: Filter by chain
        
        Returns:
            Filtered search results
        """
        results = self.history
        
        # Apply filters
        if address:
            address_lower = address.lower()
            results = [r for r in results if address_lower in r['address'].lower()]
        
        if min_risk is not None:
            results = [r for r in results if r['risk_score'] >= min_risk]
        
        if max_risk is not None:
            results = [r for r in results if r['risk_score'] <= max_risk]
        
        if chain:
            results = [r for r in results if r.get('chain') == chain]
        
        return results
    
    def export_history(
        self, 
        output_path: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Export search history to CSV
        
        Args:
            output_path: Output CSV path
            user_id: Filter by user ID (optional)
        
        Returns:
            bool indicating success
        """
        try:
            filtered = self.history
            
            if user_id:
                filtered = [s for s in filtered if s.get('user_id') == user_id]
            
            df = pd.DataFrame(filtered)
            df.to_csv(output_path, index=False)
            
            logger.info(f"✓ Exported {len(df)} search records to {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error exporting history: {e}")
            return False
    
    # ===== WATCHLIST FEATURES =====
    
    def add_to_watchlist(
        self,
        address: str,
        label: str = '',
        notes: str = '',
        current_risk_score: Optional[float] = None,
        chain: str = 'ethereum',
        user_id: Optional[str] = None
    ) -> bool:
        """
        Add address to watchlist
        
        Args:
            address: Wallet address to monitor
            label: User-defined label
            notes: Optional notes
            current_risk_score: Current risk score
            chain: Blockchain network
            user_id: Optional user identifier
        
        Returns:
            bool indicating success
        """
        # Create unique key
        key = f"{chain}:{address}:{user_id or 'default'}"
        
        self.watchlist[key] = {
            'address': address,
            'label': label,
            'notes': notes,
            'chain': chain,
            'user_id': user_id,
            'added_at': datetime.now().isoformat(),
            'last_checked': datetime.now().isoformat(),
            'risk_history': [
                {
                    'risk_score': current_risk_score,
                    'timestamp': datetime.now().isoformat()
                }
            ] if current_risk_score is not None else []
        }
        
        success = self._save_json(self.watchlist, self.watchlist_file)
        
        if success:
            logger.info(f"✓ Added to watchlist: {label or address[:10]}")
        
        return success
    
    def update_watchlist_risk(
        self,
        address: str,
        risk_score: float,
        chain: str = 'ethereum',
        user_id: Optional[str] = None
    ) -> bool:
        """
        Update risk score for watchlist address
        
        Args:
            address: Wallet address
            risk_score: New risk score
            chain: Blockchain network
            user_id: Optional user identifier
        
        Returns:
            bool indicating success
        """
        key = f"{chain}:{address}:{user_id or 'default'}"
        
        if key not in self.watchlist:
            logger.warning(f"Address not in watchlist: {address}")
            return False
        
        # Add to risk history
        self.watchlist[key]['risk_history'].append({
            'risk_score': risk_score,
            'timestamp': datetime.now().isoformat()
        })
        
        self.watchlist[key]['last_checked'] = datetime.now().isoformat()
        
        # Keep only last 100 checks per address
        if len(self.watchlist[key]['risk_history']) > 100:
            self.watchlist[key]['risk_history'] = self.watchlist[key]['risk_history'][-100:]
        
        success = self._save_json(self.watchlist, self.watchlist_file)
        
        if success:
            logger.info(f"✓ Updated watchlist: {address[:10]}... (Risk: {risk_score})")
        
        return success
    
    def get_watchlist(
        self,
        user_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get watchlist entries
        
        Args:
            user_id: Filter by user ID (optional)
        
        Returns:
            List of watchlist entries
        """
        entries = list(self.watchlist.values())
        
        # Filter by user if specified
        if user_id:
            entries = [e for e in entries if e.get('user_id') == user_id]
        
        return entries
    
    def remove_from_watchlist(
        self,
        address: str,
        chain: str = 'ethereum',
        user_id: Optional[str] = None
    ) -> bool:
        """
        Remove address from watchlist
        
        Args:
            address: Wallet address
            chain: Blockchain network
            user_id: Optional user identifier
        
        Returns:
            bool indicating success
        """
        key = f"{chain}:{address}:{user_id or 'default'}"
        
        if key in self.watchlist:
            del self.watchlist[key]
            success = self._save_json(self.watchlist, self.watchlist_file)
            
            if success:
                logger.info(f"✓ Removed from watchlist: {address[:10]}")
            
            return success
        
        return False
    
    def get_risk_trend(
        self,
        address: str,
        chain: str = 'ethereum',
        user_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get risk score trend for watchlist address
        
        Args:
            address: Wallet address
            chain: Blockchain network
            user_id: Optional user identifier
        
        Returns:
            dict with trend analysis or None
        """
        key = f"{chain}:{address}:{user_id or 'default'}"
        
        if key not in self.watchlist:
            return None
        
        risk_history = self.watchlist[key]['risk_history']
        
        if len(risk_history) < 2:
            return {
                'trend': 'insufficient_data',
                'current_risk': risk_history[0]['risk_score'] if risk_history else None,
                'change': 0,
                'history_count': len(risk_history)
            }
        
        # Calculate trend
        scores = [h['risk_score'] for h in risk_history]
        current = scores[-1]
        previous = scores[-2]
        change = current - previous
        
        # Determine trend direction
        if change > 5:
            trend = 'increasing'
        elif change < -5:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'current_risk': current,
            'previous_risk': previous,
            'change': round(change, 1),
            'min_risk': min(scores),
            'max_risk': max(scores),
            'avg_risk': round(sum(scores) / len(scores), 1),
            'history_count': len(risk_history)
        }


# Example usage
if __name__ == '__main__':
    print("User History & Watchlist Module")
    print("="*60)
    
    # Initialize
    history = UserHistory()
    
    # Add sample search
    history.add_search(
        address='0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
        risk_score=75,
        risk_category='High Risk',
        chain='ethereum'
    )
    
    # Add to watchlist
    history.add_to_watchlist(
        address='0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
        label='Suspicious Wallet',
        notes='Found in DeFi exploit transaction',
        current_risk_score=75,
        chain='ethereum'
    )
    
    print("\n✓ User History & Watchlist Module Ready")
    print("\nFeatures:")
    print("  ✓ Search history tracking")
    print("  ✓ Watchlist for monitoring")
    print("  ✓ Historical risk score tracking")
    print("  ✓ Export capabilities")
    print("  ✓ Address tagging and notes")
    print("  ✓ Risk trend analysis")
