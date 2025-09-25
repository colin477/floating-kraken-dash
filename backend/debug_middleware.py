#!/usr/bin/env python3
"""
Debug script to identify ASGI middleware issues
"""

import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DebugMiddleware:
    """Debug middleware to trace ASGI message flow"""
    
    def __init__(self, app, name="DebugMiddleware"):
        self.app = app
        self.name = name
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        logger.debug(f"{self.name}: Processing request {scope.get('path', '')}")
        
        async def debug_send(message):
            logger.debug(f"{self.name}: Sending message type: {message['type']}")
            if message["type"] == "http.response.start":
                logger.debug(f"{self.name}: Response status: {message.get('status', 'unknown')}")
                logger.debug(f"{self.name}: Response headers: {len(message.get('headers', []))} headers")
            elif message["type"] == "http.response.body":
                body_size = len(message.get("body", b""))
                more_body = message.get("more_body", False)
                logger.debug(f"{self.name}: Response body size: {body_size}, more_body: {more_body}")
            
            try:
                await send(message)
                logger.debug(f"{self.name}: Successfully sent message type: {message['type']}")
            except Exception as e:
                logger.error(f"{self.name}: Error sending message: {e}")
                raise
        
        try:
            await self.app(scope, receive, debug_send)
            logger.debug(f"{self.name}: Request completed successfully")
        except Exception as e:
            logger.error(f"{self.name}: Request failed with error: {e}")
            raise

# Test the problematic middleware in isolation
class TestCompressionMiddleware:
    """Simplified version of CompressionMiddleware for testing"""
    
    def __init__(self, app, minimum_size: int = 1024):
        self.app = app
        self.minimum_size = minimum_size
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Check if client accepts gzip
        headers = dict(scope.get("headers", []))
        accept_encoding = headers.get(b"accept-encoding", b"").decode().lower()
        supports_gzip = "gzip" in accept_encoding
        
        if not supports_gzip:
            await self.app(scope, receive, send)
            return
        
        # Capture response
        response_body = b""
        response_headers = {}
        response_status = 200
        response_started = False
        
        async def send_wrapper(message):
            nonlocal response_body, response_headers, response_status, response_started
            
            logger.debug(f"CompressionMiddleware: Received message type: {message['type']}")
            
            if message["type"] == "http.response.start":
                if response_started:
                    logger.error("CompressionMiddleware: Attempting to start response twice!")
                    raise AssertionError("Response already started")
                
                response_started = True
                response_status = message.get("status", 200)
                response_headers = dict(message.get("headers", []))
                logger.debug(f"CompressionMiddleware: Response start captured, status: {response_status}")
                
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                response_body += body
                logger.debug(f"CompressionMiddleware: Body chunk size: {len(body)}")
                
                # If this is the last chunk, send the response
                if not message.get("more_body", False):
                    logger.debug(f"CompressionMiddleware: Final body chunk, total size: {len(response_body)}")
                    
                    # Send the start message first
                    await send({
                        "type": "http.response.start",
                        "status": response_status,
                        "headers": list(response_headers.items())
                    })
                    
                    # Send the body
                    await send({
                        "type": "http.response.body",
                        "body": response_body
                    })
                    return
            
            # For streaming responses, pass through immediately
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            logger.error(f"CompressionMiddleware: Error in app processing: {e}")
            raise

if __name__ == "__main__":
    # Create a simple test app
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "Hello World", "data": "x" * 2000}  # Large enough to trigger compression
    
    # Add debug middleware
    app = DebugMiddleware(TestCompressionMiddleware(DebugMiddleware(app, "Inner")), "Outer")
    
    print("Debug middleware test app created. This would help identify ASGI issues.")