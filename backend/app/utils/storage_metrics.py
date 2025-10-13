"""
Storage metrics and monitoring utilities for cloud storage operations
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

# Configure logging
logger = logging.getLogger(__name__)

class StorageMetrics:
    """Storage metrics collection and reporting"""
    
    def __init__(self):
        self.metrics_enabled = True
        self._metrics_cache = {}
        
    def record_upload_attempt(self, user_id: str, filename: str, file_size: int):
        """Record file upload attempt"""
        if not self.metrics_enabled:
            return
            
        try:
            metric_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "filename": filename,
                "file_size": file_size,
                "operation": "upload_attempt"
            }
            
            logger.info(f"Storage upload attempt: {metric_data}")
            self._cache_metric("upload_attempts", metric_data)
            
        except Exception as e:
            logger.error(f"Error recording upload attempt metric: {e}")
    
    def record_upload_success(self, user_id: str, filename: str, file_size: int, 
                            storage_type: str, upload_duration: float):
        """Record successful file upload"""
        if not self.metrics_enabled:
            return
            
        try:
            metric_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "filename": filename,
                "file_size": file_size,
                "storage_type": storage_type,
                "upload_duration_ms": round(upload_duration * 1000, 2),
                "operation": "upload_success"
            }
            
            logger.info(f"Storage upload success: {metric_data}")
            self._cache_metric("upload_successes", metric_data)
            
        except Exception as e:
            logger.error(f"Error recording upload success metric: {e}")
    
    def record_upload_failure(self, user_id: str, filename: str, file_size: int, 
                            error_type: str, error_message: str):
        """Record failed file upload"""
        if not self.metrics_enabled:
            return
            
        try:
            metric_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "filename": filename,
                "file_size": file_size,
                "error_type": error_type,
                "error_message": error_message,
                "operation": "upload_failure"
            }
            
            logger.warning(f"Storage upload failure: {metric_data}")
            self._cache_metric("upload_failures", metric_data)
            
        except Exception as e:
            logger.error(f"Error recording upload failure metric: {e}")
    
    def record_validation_failure(self, user_id: str, filename: str, file_size: int, 
                                validation_error: str):
        """Record file validation failure"""
        if not self.metrics_enabled:
            return
            
        try:
            metric_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "filename": filename,
                "file_size": file_size,
                "validation_error": validation_error,
                "operation": "validation_failure"
            }
            
            logger.warning(f"Storage validation failure: {metric_data}")
            self._cache_metric("validation_failures", metric_data)
            
        except Exception as e:
            logger.error(f"Error recording validation failure metric: {e}")
    
    def record_delete_operation(self, user_id: str, file_url: str, success: bool):
        """Record file deletion operation"""
        if not self.metrics_enabled:
            return
            
        try:
            metric_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "file_url": file_url,
                "success": success,
                "operation": "delete_operation"
            }
            
            logger.info(f"Storage delete operation: {metric_data}")
            self._cache_metric("delete_operations", metric_data)
            
        except Exception as e:
            logger.error(f"Error recording delete operation metric: {e}")
    
    def record_presigned_url_generation(self, user_id: str, file_url: str, 
                                      expiration: int, success: bool):
        """Record presigned URL generation"""
        if not self.metrics_enabled:
            return
            
        try:
            metric_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "file_url": file_url,
                "expiration": expiration,
                "success": success,
                "operation": "presigned_url_generation"
            }
            
            logger.info(f"Storage presigned URL generation: {metric_data}")
            self._cache_metric("presigned_url_generations", metric_data)
            
        except Exception as e:
            logger.error(f"Error recording presigned URL generation metric: {e}")
    
    def _cache_metric(self, metric_type: str, metric_data: Dict[str, Any]):
        """Cache metric data for batch processing"""
        if metric_type not in self._metrics_cache:
            self._metrics_cache[metric_type] = []
        
        self._metrics_cache[metric_type].append(metric_data)
        
        # Keep only last 100 metrics of each type to prevent memory issues
        if len(self._metrics_cache[metric_type]) > 100:
            self._metrics_cache[metric_type] = self._metrics_cache[metric_type][-100:]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of cached metrics"""
        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics_enabled": self.metrics_enabled,
            "cached_metrics": {}
        }
        
        for metric_type, metrics in self._metrics_cache.items():
            summary["cached_metrics"][metric_type] = {
                "count": len(metrics),
                "latest": metrics[-1] if metrics else None
            }
        
        return summary
    
    def clear_metrics_cache(self):
        """Clear cached metrics"""
        self._metrics_cache.clear()
        logger.info("Storage metrics cache cleared")

@asynccontextmanager
async def storage_operation_timer():
    """Context manager to time storage operations"""
    start_time = time.time()
    try:
        yield start_time
    finally:
        end_time = time.time()
        duration = end_time - start_time
        logger.debug(f"Storage operation completed in {duration:.3f} seconds")

class StorageHealthMonitor:
    """Monitor storage service health and performance"""
    
    def __init__(self):
        self.health_checks = {}
        self.performance_metrics = {}
    
    async def check_storage_health(self, cloud_storage_service) -> Dict[str, Any]:
        """Comprehensive storage health check"""
        health_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": "healthy",
            "checks": {}
        }
        
        try:
            # Check 1: Service initialization
            health_data["checks"]["service_initialization"] = {
                "status": "healthy" if cloud_storage_service else "failed",
                "enabled": getattr(cloud_storage_service, 'enabled', False),
                "fallback_enabled": getattr(cloud_storage_service, 'fallback_to_local', False)
            }
            
            # Check 2: S3 client availability
            s3_client_available = getattr(cloud_storage_service, 's3_client', None) is not None
            health_data["checks"]["s3_client"] = {
                "status": "healthy" if s3_client_available else "unavailable",
                "available": s3_client_available
            }
            
            # Check 3: Configuration completeness
            config_complete = all([
                getattr(cloud_storage_service, 'aws_access_key_id', None),
                getattr(cloud_storage_service, 'aws_secret_access_key', None),
                getattr(cloud_storage_service, 's3_bucket_name', None)
            ])
            health_data["checks"]["configuration"] = {
                "status": "healthy" if config_complete else "incomplete",
                "complete": config_complete,
                "bucket_configured": bool(getattr(cloud_storage_service, 's3_bucket_name', None)),
                "credentials_configured": bool(
                    getattr(cloud_storage_service, 'aws_access_key_id', None) and
                    getattr(cloud_storage_service, 'aws_secret_access_key', None)
                )
            }
            
            # Check 4: Local storage fallback
            try:
                import os
                uploads_dir = "uploads"
                local_storage_available = os.path.exists(uploads_dir) or os.access(os.path.dirname(uploads_dir) or '.', os.W_OK)
                health_data["checks"]["local_storage_fallback"] = {
                    "status": "healthy" if local_storage_available else "failed",
                    "available": local_storage_available,
                    "uploads_dir_exists": os.path.exists(uploads_dir)
                }
            except Exception as e:
                health_data["checks"]["local_storage_fallback"] = {
                    "status": "failed",
                    "error": str(e)
                }
            
            # Check 5: S3 connectivity (if enabled and configured)
            if (getattr(cloud_storage_service, 'enabled', False) and 
                s3_client_available and 
                getattr(cloud_storage_service, 's3_bucket_name', None)):
                
                try:
                    # Test bucket access
                    cloud_storage_service.s3_client.head_bucket(
                        Bucket=cloud_storage_service.s3_bucket_name
                    )
                    health_data["checks"]["s3_connectivity"] = {
                        "status": "healthy",
                        "bucket_accessible": True
                    }
                except Exception as e:
                    health_data["checks"]["s3_connectivity"] = {
                        "status": "failed",
                        "bucket_accessible": False,
                        "error": str(e)
                    }
                    health_data["overall_status"] = "degraded"
            else:
                health_data["checks"]["s3_connectivity"] = {
                    "status": "skipped",
                    "reason": "S3 not enabled or not configured"
                }
            
            # Determine overall status
            failed_checks = [check for check in health_data["checks"].values() 
                           if check.get("status") == "failed"]
            if failed_checks:
                health_data["overall_status"] = "unhealthy"
            elif any(check.get("status") == "degraded" for check in health_data["checks"].values()):
                health_data["overall_status"] = "degraded"
            
        except Exception as e:
            health_data["overall_status"] = "unhealthy"
            health_data["error"] = str(e)
            logger.error(f"Storage health check failed: {e}")
        
        return health_data
    
    def record_performance_metric(self, operation: str, duration: float, success: bool):
        """Record performance metrics for storage operations"""
        if operation not in self.performance_metrics:
            self.performance_metrics[operation] = {
                "total_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0,
                "total_duration": 0.0,
                "average_duration": 0.0,
                "min_duration": float('inf'),
                "max_duration": 0.0
            }
        
        metrics = self.performance_metrics[operation]
        metrics["total_operations"] += 1
        
        if success:
            metrics["successful_operations"] += 1
        else:
            metrics["failed_operations"] += 1
        
        metrics["total_duration"] += duration
        metrics["average_duration"] = metrics["total_duration"] / metrics["total_operations"]
        metrics["min_duration"] = min(metrics["min_duration"], duration)
        metrics["max_duration"] = max(metrics["max_duration"], duration)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operations": self.performance_metrics.copy()
        }

# Global instances
storage_metrics = StorageMetrics()
storage_health_monitor = StorageHealthMonitor()

# Export main classes and instances
__all__ = [
    'StorageMetrics', 
    'StorageHealthMonitor', 
    'storage_metrics', 
    'storage_health_monitor',
    'storage_operation_timer'
]