"""
Token manager service for YouTube Downloader Bot.

Handles token operations and validation.
"""

import logging
from typing import Optional, List, Tuple

from bot.database import Database
from bot.config import config

logger = logging.getLogger(__name__)


class TokenManager:
    """Service for managing user tokens."""
    
    def __init__(self, db: Database):
        """
        Initialize token manager.
        
        Args:
            db: Database instance
        """
        self.db = db
    
    def get_balance(self, user_id: int) -> int:
        """Get user token balance."""
        return self.db.get_user_tokens(user_id)
    
    def has_tokens(self, user_id: int, amount: int = 1) -> bool:
        """Check if user has enough tokens."""
        return self.get_balance(user_id) >= amount
    
    def use_token(self, user_id: int, description: str = "Download") -> Tuple[bool, int]:
        """
        Use one token for download.
        
        Returns:
            Tuple of (success, remaining_balance)
        """
        if not self.has_tokens(user_id):
            return False, 0
        
        success = self.db.use_token(user_id, description)
        remaining = self.get_balance(user_id)
        
        if success:
            logger.info(f"User {user_id} used 1 token. Remaining: {remaining}")
        
        return success, remaining
    
    def add_tokens(
        self,
        user_id: int,
        amount: int,
        admin_id: int,
        description: Optional[str] = None,
    ) -> int:
        """
        Add tokens to user account.
        
        Returns:
            New balance
        """
        if description is None:
            description = f"Added {amount} token(s) by admin"
        
        new_balance = self.db.add_tokens(user_id, amount, admin_id, description)
        logger.info(f"Added {amount} tokens to user {user_id}. New balance: {new_balance}")
        
        return new_balance
    
    def get_transaction_history(self, user_id: int, limit: int = 10) -> List[dict]:
        """Get user token transaction history."""
        return self.db.get_user_token_history(user_id, limit)
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin."""
        return user_id in config.admin_user_ids
    
    def get_token_packages(self) -> List[dict]:
        """Get available token packages."""
        return [
            {
                "amount": 1,
                "price": config.token_price_1,
                "label": f"1 Token - Rp {config.token_price_1:,}".replace(",", "."),
            },
            {
                "amount": 5,
                "price": config.token_price_5,
                "label": f"5 Token - Rp {config.token_price_5:,}".replace(",", "."),
            },
            {
                "amount": 10,
                "price": config.token_price_10,
                "label": f"10 Token - Rp {config.token_price_10:,}".replace(",", "."),
            },
            {
                "amount": 25,
                "price": config.token_price_25,
                "label": f"25 Token - Rp {config.token_price_25:,}".replace(",", "."),
            },
        ]
    
    def get_price_list_text(self) -> str:
        """Get formatted price list text."""
        packages = self.get_token_packages()
        
        text = (
            "💎 *Daftar Harga Token*\n\n"
            "1 Token = 1 Video/Musik\n\n"
        )
        
        for pkg in packages:
            text += f"• {pkg['amount']} Token: *Rp {pkg['price']:,}*\n".replace(",", ".")
        
        text += (
            f"\n━━━━━━━━━━━━━━━━━━\n"
            f"📞 *Hubungi Admin untuk Pembelian:*\n"
            f"• Telegram: {config.admin_contact}\n"
        )
        
        if config.admin_whatsapp:
            text += f"• WhatsApp: {config.admin_whatsapp}\n"
        
        text += (
            f"\n💡 *Cara Pembelian:*\n"
            f"1. Transfer ke rekening admin\n"
            f"2. Kirim bukti transfer\n"
            f"3. Token akan ditambahkan ke akun Anda\n"
        )
        
        return text
