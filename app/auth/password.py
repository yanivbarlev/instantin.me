from passlib.context import CryptContext
from typing import Optional
import secrets
import string
import re
import logging

logger = logging.getLogger(__name__)

# Configure password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Higher rounds for better security (default is 12)
)


class PasswordManager:
    """
    Password management utility for InstantIn.me platform.
    Handles hashing, verification, generation, and validation of passwords.
    """
    
    def __init__(self):
        self.context = pwd_context
    
    def hash_password(self, password: str) -> str:
        """
        Hash a plain text password using bcrypt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password string
            
        Example:
            pm = PasswordManager()
            hashed = pm.hash_password("MySecurePassword123")
        """
        try:
            hashed = self.context.hash(password)
            logger.info("Password hashed successfully")
            return hashed
        except Exception as e:
            logger.error(f"Failed to hash password: {e}")
            raise ValueError("Password hashing failed")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against a hashed password.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
            
        Example:
            pm = PasswordManager()
            is_valid = pm.verify_password("MyPassword123", stored_hash)
        """
        try:
            is_valid = self.context.verify(plain_password, hashed_password)
            if is_valid:
                logger.info("Password verification successful")
            else:
                logger.warning("Password verification failed")
            return is_valid
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def needs_update(self, hashed_password: str) -> bool:
        """
        Check if a hashed password needs to be updated (rehashed).
        This happens when the hashing algorithm or parameters change.
        
        Args:
            hashed_password: Existing hashed password
            
        Returns:
            True if password needs rehashing, False otherwise
        """
        try:
            return self.context.needs_update(hashed_password)
        except Exception as e:
            logger.error(f"Error checking if password needs update: {e}")
            return False
    
    def validate_password_strength(self, password: str) -> dict:
        """
        Validate password strength against security requirements.
        
        Args:
            password: Plain text password to validate
            
        Returns:
            Dictionary with validation results:
            {
                "is_valid": bool,
                "errors": list of error messages,
                "score": int (0-5, higher is better),
                "suggestions": list of improvement suggestions
            }
        """
        errors = []
        suggestions = []
        score = 0
        
        # Length check
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        elif len(password) >= 12:
            score += 1
            if len(password) >= 16:
                score += 1
        
        # Character type checks
        has_lower = bool(re.search(r'[a-z]', password))
        has_upper = bool(re.search(r'[A-Z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        if not has_lower:
            errors.append("Password must contain at least one lowercase letter")
        else:
            score += 1
            
        if not has_upper:
            errors.append("Password must contain at least one uppercase letter")
        else:
            score += 1
            
        if not has_digit:
            errors.append("Password must contain at least one digit")
        else:
            score += 1
            
        if not has_special:
            suggestions.append("Consider adding special characters (!@#$%^&*) for stronger security")
        else:
            score += 1
        
        # Common patterns check
        if re.search(r'(.)\1{2,}', password):  # Three or more repeated characters
            suggestions.append("Avoid repeating the same character multiple times")
            score = max(0, score - 1)
        
        if re.search(r'(012|123|234|345|456|567|678|789|890)', password):
            suggestions.append("Avoid sequential numbers")
            score = max(0, score - 1)
        
        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
            suggestions.append("Avoid sequential letters")
            score = max(0, score - 1)
        
        # Common words check (basic)
        common_words = ['password', 'admin', 'user', 'login', 'welcome', 'qwerty', 'letmein']
        if any(word in password.lower() for word in common_words):
            errors.append("Password contains common words that are easily guessable")
            score = max(0, score - 2)
        
        # Additional suggestions based on score
        if score < 3:
            suggestions.append("Consider using a longer password with mixed characters")
        if score >= 4:
            suggestions.append("Good password strength!")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "score": score,
            "suggestions": suggestions
        }
    
    def generate_secure_password(self, length: int = 16) -> str:
        """
        Generate a cryptographically secure random password.
        
        Args:
            length: Length of password to generate (minimum 12)
            
        Returns:
            Randomly generated secure password
            
        Example:
            pm = PasswordManager()
            password = pm.generate_secure_password(16)
        """
        if length < 12:
            raise ValueError("Password length must be at least 12 characters")
        
        # Ensure we have at least one character from each required type
        characters = (
            string.ascii_lowercase +
            string.ascii_uppercase +
            string.digits +
            "!@#$%^&*(),.?\":{}|<>"
        )
        
        # Guarantee at least one of each required type
        password_chars = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*(),.?\":{}|<>")
        ]
        
        # Fill the rest randomly
        for _ in range(length - 4):
            password_chars.append(secrets.choice(characters))
        
        # Shuffle to avoid predictable patterns
        secrets.SystemRandom().shuffle(password_chars)
        
        password = ''.join(password_chars)
        logger.info(f"Generated secure password of length {length}")
        return password
    
    def generate_temporary_password(self) -> str:
        """
        Generate a temporary password for password reset flows.
        
        Returns:
            8-character temporary password (users should change immediately)
        """
        # For temporary passwords, use a shorter length but still secure
        return self.generate_secure_password(12)


# Global password manager instance
password_manager = PasswordManager()


def hash_password(password: str) -> str:
    """
    Convenience function to hash a password.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
    """
    return password_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Convenience function to verify a password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return password_manager.verify_password(plain_password, hashed_password)


def validate_password_strength(password: str) -> dict:
    """
    Convenience function to validate password strength.
    
    Args:
        password: Plain text password to validate
        
    Returns:
        Dictionary with validation results
    """
    return password_manager.validate_password_strength(password)


def generate_secure_password(length: int = 16) -> str:
    """
    Convenience function to generate a secure password.
    
    Args:
        length: Length of password to generate (minimum 12)
        
    Returns:
        Randomly generated secure password
    """
    return password_manager.generate_secure_password(length)


def password_needs_update(hashed_password: str) -> bool:
    """
    Convenience function to check if password needs rehashing.
    
    Args:
        hashed_password: Existing hashed password
        
    Returns:
        True if password needs rehashing, False otherwise
    """
    return password_manager.needs_update(hashed_password)


def create_user_password(plain_password: str) -> str:
    """
    Create a hashed password for a new user with validation.
    
    Args:
        plain_password: User's chosen password
        
    Returns:
        Hashed password ready for database storage
        
    Raises:
        ValueError: If password doesn't meet strength requirements
    """
    # Validate password strength
    validation = validate_password_strength(plain_password)
    
    if not validation["is_valid"]:
        error_msg = "Password validation failed: " + "; ".join(validation["errors"])
        logger.warning(f"Password creation failed: {error_msg}")
        raise ValueError(error_msg)
    
    # Hash the validated password
    hashed = hash_password(plain_password)
    logger.info("User password created and hashed successfully")
    return hashed


def authenticate_user_password(plain_password: str, stored_hash: str) -> tuple[bool, Optional[str]]:
    """
    Authenticate a user's password and optionally return updated hash.
    
    Args:
        plain_password: Password provided by user
        stored_hash: Hashed password from database
        
    Returns:
        Tuple of (is_authenticated, new_hash_if_needed)
        - is_authenticated: True if password is correct
        - new_hash_if_needed: New hash if password needs updating, None otherwise
    """
    # Verify the password
    is_valid = verify_password(plain_password, stored_hash)
    
    if not is_valid:
        return False, None
    
    # Check if hash needs updating
    if password_needs_update(stored_hash):
        logger.info("Password hash needs updating, generating new hash")
        new_hash = hash_password(plain_password)
        return True, new_hash
    
    return True, None


# Password constants for reference
PASSWORD_MIN_LENGTH = 8
PASSWORD_RECOMMENDED_LENGTH = 12
PASSWORD_STRONG_LENGTH = 16

# Character sets for reference
LOWERCASE_CHARS = string.ascii_lowercase
UPPERCASE_CHARS = string.ascii_uppercase
DIGIT_CHARS = string.digits
SPECIAL_CHARS = "!@#$%^&*(),.?\":{}|<>" 