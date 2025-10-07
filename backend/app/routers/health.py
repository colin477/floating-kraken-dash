"""
Health check and system status endpoints
"""

from fastapi import APIRouter
from typing import Dict, Any
from app.models.responses import SuccessResponse

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return SuccessResponse(message="EZ Eatin' API is healthy")


@router.get("/ocr")
async def ocr_health_check() -> Dict[str, Any]:
    """Check OCR service health and configuration status"""
    try:
        from app.utils.ocr_service import ocr_service
        
        status = ocr_service.get_service_status()
        
        # Determine overall OCR health
        if status["enabled"] and (status["client_initialized"] or status["demo_mode"]):
            health_status = "healthy"
            message = "OCR service is operational"
        elif status["enabled"] and status["demo_mode"]:
            health_status = "demo"
            message = "OCR service running in demo mode"
        elif not status["enabled"]:
            health_status = "disabled"
            message = "OCR service is disabled"
        else:
            health_status = "unhealthy"
            message = "OCR service has configuration issues"
        
        return {
            "status": health_status,
            "message": message,
            "details": status,
            "recommendations": _get_ocr_recommendations(status)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to check OCR service: {str(e)}",
            "details": {},
            "recommendations": ["Check OCR service configuration"]
        }


def _get_ocr_recommendations(status: Dict[str, Any]) -> list:
    """Generate recommendations based on OCR service status"""
    recommendations = []
    
    if not status["enabled"]:
        recommendations.append("Set OCR_ENABLED=true in environment variables to enable OCR functionality")
    
    if status["enabled"] and not status["credentials_configured"]:
        recommendations.append("Configure Google Vision API credentials for real OCR processing")
        recommendations.append("See GOOGLE_VISION_API_SETUP_GUIDE.md for setup instructions")
    
    if status["enabled"] and status["credentials_configured"] and not status["client_initialized"]:
        recommendations.append("Check Google Vision API credentials and permissions")
    
    if status["demo_mode"]:
        recommendations.append("Currently using demo mode with mock OCR data")
    
    if not status["fallback_enabled"]:
        recommendations.append("Consider enabling OCR_FALLBACK_ENABLED for better reliability")
    
    return recommendations


@router.get("/database")
async def database_health_check():
    """Check database connection health"""
    try:
        from app.database import get_collection
        
        # Try to access a collection to test connection
        collection = await get_collection("users")
        
        # Simple ping test
        await collection.find_one({}, {"_id": 1})
        
        return {
            "status": "healthy",
            "message": "Database connection is operational",
            "database": "MongoDB"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
            "database": "MongoDB"
        }


@router.get("/storage")
async def storage_health_check():
    """Check cloud storage service health"""
    try:
        from app.utils.cloud_storage import cloud_storage_service
        
        # Get storage service status
        storage_type = "local" if not hasattr(cloud_storage_service, 'client') or cloud_storage_service.client is None else "cloud"
        
        return {
            "status": "healthy",
            "message": f"Storage service is operational ({storage_type})",
            "storage_type": storage_type,
            "fallback_enabled": getattr(cloud_storage_service, 'fallback_enabled', True)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Storage service check failed: {str(e)}",
            "storage_type": "unknown"
        }


@router.get("/system")
async def system_health_check():
    """Comprehensive system health check"""
    try:
        # Check all subsystems
        ocr_health = await ocr_health_check()
        db_health = await database_health_check()
        storage_health = await storage_health_check()
        
        # Determine overall system health
        all_healthy = all(
            health.get("status") in ["healthy", "demo"] 
            for health in [ocr_health, db_health, storage_health]
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "message": "System status check completed",
            "services": {
                "ocr": ocr_health,
                "database": db_health,
                "storage": storage_health
            },
            "timestamp": "2024-01-01T00:00:00Z"  # This would be actual timestamp in production
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"System health check failed: {str(e)}",
            "services": {}
        }