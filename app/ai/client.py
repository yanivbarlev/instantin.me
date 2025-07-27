"""
Groq API Client for InstantIn.me

This module provides the core AI service integration with Groq API,
including prompt management, response handling, and error recovery.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging

try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None

from app.ai.config import ai_config, AIFeature
from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class GroqError(Exception):
    """Custom exception for Groq API errors"""
    def __init__(self, message: str, error_code: Optional[str] = None, retry_after: Optional[int] = None):
        super().__init__(message)
        self.error_code = error_code
        self.retry_after = retry_after


class GroqClient:
    """
    Async Groq API client with retry logic, rate limiting, and error handling.
    
    Features:
    - Automatic retry with exponential backoff
    - Rate limiting protection
    - Structured prompt management
    - Response validation and parsing
    - Comprehensive error handling
    """
    
    def __init__(self):
        if not AsyncGroq:
            raise ImportError("groq package not installed. Run: pip install groq")
        
        if not settings.groq_api_key:
            logger.warning("Groq API key not configured - AI features will be disabled")
            self.client = None
        else:
            self.client = AsyncGroq(api_key=settings.groq_api_key)
        
        self.config = ai_config.groq_config
        self._last_request_time = 0
        self._request_count = 0
        self._rate_limit_window = 60  # 1 minute window
        self._max_requests_per_minute = 50
    
    async def is_available(self) -> bool:
        """Check if Groq client is available and configured"""
        return self.client is not None and settings.groq_configured
    
    async def _wait_for_rate_limit(self) -> None:
        """Implement basic rate limiting"""
        current_time = time.time()
        
        # Reset counter if window expired
        if current_time - self._last_request_time > self._rate_limit_window:
            self._request_count = 0
            self._last_request_time = current_time
        
        # Check if we're hitting rate limits
        if self._request_count >= self._max_requests_per_minute:
            wait_time = self._rate_limit_window - (current_time - self._last_request_time)
            if wait_time > 0:
                logger.warning(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
                self._request_count = 0
                self._last_request_time = time.time()
        
        self._request_count += 1
    
    async def _make_request_with_retry(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        max_retries: int = 3
    ) -> str:
        """
        Make a request to Groq API with automatic retry logic.
        
        Args:
            prompt: The prompt to send to the AI
            max_tokens: Maximum tokens to generate
            temperature: Temperature for response randomness
            max_retries: Maximum number of retry attempts
            
        Returns:
            str: The AI response content
            
        Raises:
            GroqError: When all retries are exhausted or unrecoverable error
        """
        if not await self.is_available():
            raise GroqError("Groq API not available - check configuration")
        
        # Use config defaults if not specified
        max_tokens = max_tokens or self.config["max_tokens"]
        temperature = temperature or self.config["temperature"]
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                # Rate limiting
                await self._wait_for_rate_limit()
                
                # Make the API call
                response = await self.client.chat.completions.create(
                    model=self.config["model"],
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=self.config["timeout"]
                )
                
                # Extract and validate response
                if not response.choices or not response.choices[0].message.content:
                    raise GroqError("Empty response from Groq API")
                
                content = response.choices[0].message.content.strip()
                logger.info(f"Groq API call successful: {len(content)} characters generated")
                
                return content
                
            except Exception as e:
                last_error = e
                
                # Check if this is a retryable error
                if attempt < max_retries:
                    # Exponential backoff
                    wait_time = (2 ** attempt) + (0.1 * attempt)
                    logger.warning(f"Groq API error (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    logger.info(f"Retrying in {wait_time:.1f} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Max retries reached
                    logger.error(f"Groq API call failed after {max_retries + 1} attempts: {e}")
                    break
        
        # All retries exhausted
        if isinstance(last_error, Exception):
            raise GroqError(f"Groq API call failed: {last_error}") from last_error
        else:
            raise GroqError("Groq API call failed for unknown reason")
    
    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        feature: Optional[AIFeature] = None
    ) -> str:
        """
        Generate text using Groq API with validation.
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens to generate
            temperature: Temperature for randomness
            feature: AI feature being used (for logging/analytics)
            
        Returns:
            str: Generated text content
            
        Raises:
            GroqError: When generation fails
        """
        start_time = time.time()
        
        try:
            # Validate prompt
            if not prompt or not prompt.strip():
                raise GroqError("Empty prompt provided")
            
            # Log the request
            logger.info(f"Groq text generation request: {len(prompt)} chars prompt, feature: {feature}")
            
            # Make the request
            response = await self._make_request_with_retry(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Log success metrics
            duration = time.time() - start_time
            logger.info(f"Text generation completed in {duration:.2f}s: {len(response)} chars")
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Text generation failed after {duration:.2f}s: {e}")
            raise GroqError(f"Text generation failed: {e}") from e
    
    async def generate_json(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        feature: Optional[AIFeature] = None
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response using Groq API.
        
        Args:
            prompt: The prompt requesting JSON output
            max_tokens: Maximum tokens to generate
            temperature: Temperature for randomness
            feature: AI feature being used
            
        Returns:
            Dict: Parsed JSON response
            
        Raises:
            GroqError: When generation or JSON parsing fails
        """
        try:
            # Add JSON formatting instruction to prompt
            json_prompt = f"{prompt}\n\nPlease respond with valid JSON only. Do not include any explanation or markdown formatting."
            
            # Generate response
            response = await self.generate_text(
                prompt=json_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                feature=feature
            )
            
            # Clean response (remove markdown code blocks if present)
            clean_response = response
            if "```json" in response:
                clean_response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                clean_response = response.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            try:
                parsed_json = json.loads(clean_response)
                logger.info(f"JSON generation successful: {len(str(parsed_json))} chars")
                return parsed_json
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                logger.error(f"Raw response: {response[:500]}...")
                raise GroqError(f"Invalid JSON response: {e}")
                
        except GroqError:
            raise
        except Exception as e:
            raise GroqError(f"JSON generation failed: {e}") from e
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the Groq API.
        
        Returns:
            Dict: Health status information
        """
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "available": False,
            "configured": settings.groq_configured,
            "model": self.config["model"],
            "error": None,
            "response_time": None
        }
        
        if not await self.is_available():
            status["error"] = "Groq API not configured"
            return status
        
        try:
            start_time = time.time()
            
            # Simple test prompt
            test_response = await self.generate_text(
                prompt="Say 'Hello, InstantIn.me!' in exactly those words.",
                max_tokens=10,
                temperature=0.1
            )
            
            response_time = time.time() - start_time
            
            status.update({
                "available": True,
                "response_time": round(response_time, 2),
                "test_response": test_response[:50]  # First 50 chars
            })
            
        except Exception as e:
            status.update({
                "available": False,
                "error": str(e),
                "response_time": time.time() - start_time if 'start_time' in locals() else None
            })
        
        return status


# Global Groq client instance
groq_client = GroqClient()


# Convenience functions for easy import
async def generate_text(prompt: str, feature: Optional[AIFeature] = None, **kwargs) -> str:
    """Generate text using Groq API"""
    return await groq_client.generate_text(prompt=prompt, feature=feature, **kwargs)


async def generate_json(prompt: str, feature: Optional[AIFeature] = None, **kwargs) -> Dict[str, Any]:
    """Generate JSON using Groq API"""
    return await groq_client.generate_json(prompt=prompt, feature=feature, **kwargs)


async def is_ai_service_available() -> bool:
    """Check if AI service is available"""
    return await groq_client.is_available()


async def get_ai_health_status() -> Dict[str, Any]:
    """Get AI service health status"""
    return await groq_client.health_check()


if __name__ == "__main__":
    # Test the client when run directly
    async def test_client():
        print("🤖 Testing Groq API Client...")
        
        health = await get_ai_health_status()
        print(f"Health Status: {health}")
        
        if health["available"]:
            print("\n✅ Testing text generation...")
            response = await generate_text("Write a brief welcome message for InstantIn.me users.")
            print(f"Response: {response}")
        else:
            print("❌ Groq API not available")
    
    # Run test if executed directly
    asyncio.run(test_client()) 