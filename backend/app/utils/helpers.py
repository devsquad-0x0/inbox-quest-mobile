import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional

def generate_referral_code(length: int = 8) -> str:
    """Generate a unique referral code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def generate_verification_code(length: int = 6) -> str:
    """Generate a 6-digit verification code"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def generate_nonce(length: int = 32) -> str:
    """Generate a random nonce for tracking tokens"""
    return secrets.token_urlsafe(length)

def hash_string(text: str) -> str:
    """Generate SHA256 hash of a string"""
    return hashlib.sha256(text.encode()).hexdigest()

def get_level_from_xp(xp: int, thresholds: list) -> int:
    """Calculate level from XP using thresholds"""
    level = 1
    for threshold in thresholds:
        if xp >= threshold:
            level += 1
        else:
            break
    return min(level, len(thresholds))

def get_xp_for_level(level: int, thresholds: list) -> int:
    """Get XP required for a specific level"""
    if level <= 1:
        return 0
    if level > len(thresholds):
        return thresholds[-1]
    return thresholds[level - 1]

def calculate_xp_progress(current_xp: int, current_level: int, thresholds: list) -> tuple:
    """Calculate XP progress to next level"""
    if current_level >= len(thresholds):
        return (0, 100)  # Max level
    
    current_level_xp = get_xp_for_level(current_level, thresholds)
    next_level_xp = get_xp_for_level(current_level + 1, thresholds)
    xp_needed = next_level_xp - current_level_xp
    xp_progress = current_xp - current_level_xp
    progress_percent = int((xp_progress / xp_needed) * 100) if xp_needed > 0 else 100
    
    return (xp_needed - xp_progress, min(progress_percent, 100))
