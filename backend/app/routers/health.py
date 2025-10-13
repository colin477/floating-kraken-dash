"""
Health check and system status endpoints
"""

from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime
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
    """Check database connection health with detailed connection pool stats"""
    try:
        from app.database import check_connection_health, get_connection_stats
        
        # Check connection health using our new monitoring
        is_healthy = await check_connection_health()
        
        # Get detailed connection statistics
        connection_stats = await get_connection_stats()
        
        if is_healthy:
            return {
                "status": "healthy",
                "message": "Database connection is operational",
                "database": "MongoDB",
                "connection_stats": connection_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "unhealthy",
                "message": "Database connection health check failed",
                "database": "MongoDB",
                "connection_stats": connection_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database health check error: {str(e)}",
            "database": "MongoDB",
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/storage")
async def storage_health_check():
    """Enhanced cloud storage service health check"""
    try:
        from app.utils.cloud_storage import cloud_storage_service
        from app.utils.storage_metrics import storage_health_monitor

        # Get comprehensive health check
        health_data = await storage_health_monitor.check_storage_health(cloud_storage_service)
        
        # Add basic compatibility fields for existing clients
        health_data["message"] = f"Storage service is {health_data['overall_status']}"
        health_data["storage_type"] = "cloud" if cloud_storage_service.is_cloud_storage_enabled() else "local"
        health_data["fallback_enabled"] = getattr(cloud_storage_service, 'fallback_to_local', True)
        
        # Set HTTP status based on health
        health_data["status"] = health_data["overall_status"]
        
        return health_data

    except Exception as e:
        return {
            "status": "unhealthy",
            "overall_status": "unhealthy",
            "message": f"Storage service check failed: {str(e)}",
            "storage_type": "unknown",
            "error": str(e),
            "timestamp": "2025-01-01T00:00:00Z"
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
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"System health check failed: {str(e)}",
            "services": {}
        }