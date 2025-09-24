from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any

from auth import AuthManager
from models.user import User
from models.subdomain import Subdomain
from config import config

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin login page"""
    return templates.TemplateResponse("admin/login.html", {
        "request": request
    })

@router.post("/login")
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Admin login handler"""
    if AuthManager.admin_login(request, username, password):
        return RedirectResponse("/admin", status_code=302)
    else:
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "error": "Noto'g'ri foydalanuvchi nomi yoki parol"
        })

@router.post("/logout")
async def admin_logout(request: Request):
    """Admin logout"""
    AuthManager.admin_logout(request)
    return RedirectResponse("/", status_code=302)

@router.get("/", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """Admin panel main page"""
    try:
        # Check admin privileges
        user = AuthManager.require_admin(request)
        
        return templates.TemplateResponse("admin/panel.html", {
            "request": request,
            "user": user.to_dict() if hasattr(user, 'to_dict') else {
                'username': user.username,
                'is_admin': True
            }
        })
    except HTTPException as e:
        if e.status_code == 403:
            return RedirectResponse("/admin/login", status_code=302)
        raise

@router.get("/stats", response_class=JSONResponse)
async def get_admin_stats(request: Request):
    """Get server statistics for admin panel"""
    AuthManager.require_admin(request)
    
    try:
        # System statistics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database statistics
        all_users = User.get_all()
        all_subdomains = Subdomain.get_all()
        
        # Calculate total file sizes
        total_size = 0
        total_files = 0
        for subdomain in all_subdomains:
            total_size += subdomain.get_file_size()
            total_files += subdomain.get_file_count()
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_users = [u for u in all_users if u.created_at and u.created_at > week_ago]
        recent_subdomains = [s for s in all_subdomains if s.created_at and s.created_at > week_ago]
        
        # Sites folder size
        sites_folder_size = 0
        if os.path.exists(config.SITES_FOLDER):
            for dirpath, dirnames, filenames in os.walk(config.SITES_FOLDER):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        sites_folder_size += os.path.getsize(filepath)
        
        stats = {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_total": memory.total,
                "memory_used": memory.used,
                "memory_percent": memory.percent,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "disk_percent": (disk.used / disk.total) * 100,
                "sites_folder_size": sites_folder_size
            },
            "users": {
                "total": len(all_users),
                "recent": len(recent_users),
                "admins": 1  # Only one pre-configured admin
            },
            "subdomains": {
                "total": len(all_subdomains),
                "recent": len(recent_subdomains),
                "total_size": total_size,
                "total_files": total_files
            },
            "activity": {
                "new_users_week": len(recent_users),
                "new_sites_week": len(recent_subdomains)
            }
        }
        
        return {"success": True, "stats": stats}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@router.get("/users", response_class=JSONResponse)
async def get_all_users(request: Request):
    """Get all users for admin management"""
    # Check admin privileges
    AuthManager.require_admin(request)
    
    try:
        users = User.get_all()
        users_data = []
        
        for user in users:
            user_dict = user.to_dict()
            user_dict['subdomain_count'] = len(user.get_subdomains())
            users_data.append(user_dict)
        
        return {"success": True, "users": users_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting users: {str(e)}")

@router.get("/subdomains", response_class=JSONResponse)
async def get_all_subdomains(request: Request):
    """Get all subdomains for admin management"""
    # Check admin privileges
    AuthManager.require_admin(request)
    
    try:
        subdomains = Subdomain.get_all()
        subdomains_data = []
        
        for subdomain in subdomains:
            subdomain_dict = subdomain.to_dict()
            
            # Add user information
            user = User.get_by_id(subdomain.user_id) if subdomain.user_id else None
            subdomain_dict['user'] = user.to_dict() if user else None
            
            subdomains_data.append(subdomain_dict)
        
        return {"success": True, "subdomains": subdomains_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting subdomains: {str(e)}")

@router.delete("/subdomain/{subdomain_id}")
async def admin_delete_subdomain(request: Request, subdomain_id: int):
    """Admin delete subdomain"""
    # Check admin privileges
    AuthManager.require_admin(request)
    
    try:
        subdomain = Subdomain.get_by_id(subdomain_id)
        if not subdomain:
            raise HTTPException(status_code=404, detail="Subdomain not found")
        
        success = subdomain.delete()
        if success:
            return {"success": True, "message": "Subdomain deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete subdomain")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting subdomain: {str(e)}")

@router.delete("/user/{user_id}")
async def admin_delete_user(request: Request, user_id: int):
    """Admin delete user and all their subdomains"""
    # Check admin privileges
    current_admin = AuthManager.require_admin(request)
    
    try:
        user = User.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent deleting self
        if user.id == current_admin.id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        success = user.delete()
        if success:
            return {"success": True, "message": "User deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete user")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

@router.get("/system-info", response_class=JSONResponse)
async def get_system_info(request: Request):
    """Get detailed system information"""
    # Check admin privileges
    AuthManager.require_admin(request)
    
    try:
        # System information
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.utcnow() - boot_time
        
        # Network information
        network_stats = psutil.net_io_counters()
        
        # Process information
        process_count = len(psutil.pids())
        
        system_info = {
            "hostname": os.uname().nodename,
            "platform": os.uname().system,
            "architecture": os.uname().machine,
            "boot_time": boot_time.isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "process_count": process_count,
            "network": {
                "bytes_sent": network_stats.bytes_sent,
                "bytes_recv": network_stats.bytes_recv,
                "packets_sent": network_stats.packets_sent,
                "packets_recv": network_stats.packets_recv
            }
        }
        
        return {"success": True, "system_info": system_info}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system info: {str(e)}")

@router.get("/logs", response_class=JSONResponse)
async def get_system_logs(request: Request, lines: int = 100):
    """Get recent system logs"""
    # Check admin privileges
    AuthManager.require_admin(request)
    
    try:
        logs = []
        log_files = [
            "/var/log/nginx/access.log",
            "/var/log/nginx/error.log",
            "logs/app.log"
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        file_lines = f.readlines()
                        recent_lines = file_lines[-lines:] if len(file_lines) > lines else file_lines
                        
                        for line in recent_lines:
                            logs.append({
                                "file": log_file,
                                "content": line.strip(),
                                "timestamp": datetime.utcnow().isoformat()
                            })
                except Exception as e:
                    logs.append({
                        "file": log_file,
                        "content": f"Error reading log: {str(e)}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
        
        return {"success": True, "logs": logs}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")

@router.get("/activity", response_class=JSONResponse)
async def get_user_activity(request: Request, days: int = 7):
    """Get user activity statistics for the last N days"""
    # Check admin privileges
    AuthManager.require_admin(request)
    
    try:
        # Get activity data for the specified number of days
        activity_data = []
        
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i)
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Count new users for this day
            all_users = User.get_all()
            new_users = len([u for u in all_users if u.created_at and 
                           start_of_day <= u.created_at <= end_of_day])
            
            # Count new subdomains for this day
            all_subdomains = Subdomain.get_all()
            new_subdomains = len([s for s in all_subdomains if s.created_at and 
                                start_of_day <= s.created_at <= end_of_day])
            
            activity_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "new_users": new_users,
                "new_subdomains": new_subdomains
            })
        
        # Reverse to show oldest first
        activity_data.reverse()
        
        return {"success": True, "activity": activity_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting activity: {str(e)}")

@router.get("/resource-usage", response_class=JSONResponse)
async def get_resource_usage(request: Request):
    """Get detailed resource usage statistics"""
    # Check admin privileges
    AuthManager.require_admin(request)
    
    try:
        # CPU information
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        cpu_times = psutil.cpu_times()
        
        # Memory information
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk information
        disk_usage = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        # Network information
        network_io = psutil.net_io_counters()
        
        # Process information
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                proc_info = proc.info
                if proc_info['cpu_percent'] > 0 or proc_info['memory_percent'] > 0:
                    processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        top_processes = processes[:10]  # Top 10 processes
        
        resource_usage = {
            "cpu": {
                "count": cpu_count,
                "frequency": {
                    "current": cpu_freq.current if cpu_freq else None,
                    "min": cpu_freq.min if cpu_freq else None,
                    "max": cpu_freq.max if cpu_freq else None
                },
                "times": {
                    "user": cpu_times.user,
                    "system": cpu_times.system,
                    "idle": cpu_times.idle
                }
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "free": memory.free,
                "percent": memory.percent,
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "free": swap.free,
                    "percent": swap.percent
                }
            },
            "disk": {
                "usage": {
                    "total": disk_usage.total,
                    "used": disk_usage.used,
                    "free": disk_usage.free,
                    "percent": (disk_usage.used / disk_usage.total) * 100
                },
                "io": {
                    "read_count": disk_io.read_count if disk_io else 0,
                    "write_count": disk_io.write_count if disk_io else 0,
                    "read_bytes": disk_io.read_bytes if disk_io else 0,
                    "write_bytes": disk_io.write_bytes if disk_io else 0
                }
            },
            "network": {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv,
                "errin": network_io.errin,
                "errout": network_io.errout,
                "dropin": network_io.dropin,
                "dropout": network_io.dropout
            },
            "processes": top_processes
        }
        
        return {"success": True, "resource_usage": resource_usage}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting resource usage: {str(e)}")

@router.get("/storage-analysis", response_class=JSONResponse)
async def get_storage_analysis(request: Request):
    """Get detailed storage analysis for all subdomains"""
    # Check admin privileges
    AuthManager.require_admin(request)
    
    try:
        all_subdomains = Subdomain.get_all()
        
        # Analyze storage usage
        storage_stats = {
            "total_subdomains": len(all_subdomains),
            "total_size": 0,
            "total_files": 0,
            "size_distribution": {
                "small": 0,    # < 1MB
                "medium": 0,   # 1MB - 10MB
                "large": 0,    # 10MB - 100MB
                "xlarge": 0    # > 100MB
            },
            "file_types": {},
            "largest_subdomains": [],
            "empty_subdomains": []
        }
        
        subdomain_sizes = []
        
        for subdomain in all_subdomains:
            size = subdomain.get_file_size()
            file_count = subdomain.get_file_count()
            
            storage_stats["total_size"] += size
            storage_stats["total_files"] += file_count
            
            # Size distribution
            if size < 1024 * 1024:  # < 1MB
                storage_stats["size_distribution"]["small"] += 1
            elif size < 10 * 1024 * 1024:  # < 10MB
                storage_stats["size_distribution"]["medium"] += 1
            elif size < 100 * 1024 * 1024:  # < 100MB
                storage_stats["size_distribution"]["large"] += 1
            else:  # > 100MB
                storage_stats["size_distribution"]["xlarge"] += 1
            
            # Track empty subdomains
            if file_count == 0:
                storage_stats["empty_subdomains"].append({
                    "id": subdomain.id,
                    "name": subdomain.subdomain_name,
                    "user_id": subdomain.user_id
                })
            
            # Collect for largest subdomains
            subdomain_sizes.append({
                "id": subdomain.id,
                "name": subdomain.subdomain_name,
                "user_id": subdomain.user_id,
                "size": size,
                "file_count": file_count
            })
            
            # Analyze file types
            if os.path.exists(subdomain.file_path):
                for root, dirs, files in os.walk(subdomain.file_path):
                    for file in files:
                        ext = os.path.splitext(file)[1].lower()
                        if ext:
                            storage_stats["file_types"][ext] = storage_stats["file_types"].get(ext, 0) + 1
        
        # Get largest subdomains
        subdomain_sizes.sort(key=lambda x: x["size"], reverse=True)
        storage_stats["largest_subdomains"] = subdomain_sizes[:10]
        
        return {"success": True, "storage_analysis": storage_stats}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing storage: {str(e)}")

@router.get("/performance-metrics", response_class=JSONResponse)
async def get_performance_metrics(request: Request):
    """Get performance metrics and health indicators"""
    # Check admin privileges
    AuthManager.require_admin(request)
    
    try:
        # Load averages (Unix-like systems)
        load_avg = None
        try:
            load_avg = os.getloadavg()
        except (OSError, AttributeError):
            # Not available on Windows
            pass
        
        # Memory pressure indicators
        memory = psutil.virtual_memory()
        memory_pressure = "low"
        if memory.percent > 90:
            memory_pressure = "critical"
        elif memory.percent > 75:
            memory_pressure = "high"
        elif memory.percent > 50:
            memory_pressure = "medium"
        
        # Disk I/O pressure
        disk_usage = psutil.disk_usage('/')
        disk_pressure = "low"
        if disk_usage.used / disk_usage.total > 0.95:
            disk_pressure = "critical"
        elif disk_usage.used / disk_usage.total > 0.85:
            disk_pressure = "high"
        elif disk_usage.used / disk_usage.total > 0.70:
            disk_pressure = "medium"
        
        # Check if critical services are running
        services_status = {}
        try:
            # Check nginx process
            nginx_running = any("nginx" in p.name().lower() for p in psutil.process_iter())
            services_status["nginx"] = nginx_running
        except:
            services_status["nginx"] = False
        
        # Application health indicators
        all_subdomains = Subdomain.get_all()
        all_users = User.get_all()
        
        # Calculate average subdomain size
        total_size = sum(s.get_file_size() for s in all_subdomains)
        avg_subdomain_size = total_size / len(all_subdomains) if all_subdomains else 0
        
        performance_metrics = {
            "system_health": {
                "memory_pressure": memory_pressure,
                "disk_pressure": disk_pressure,
                "load_average": load_avg,
                "services": services_status
            },
            "application_metrics": {
                "total_users": len(all_users),
                "total_subdomains": len(all_subdomains),
                "average_subdomain_size": avg_subdomain_size,
                "total_storage_used": total_size
            },
            "recommendations": []
        }
        
        # Generate recommendations
        if memory_pressure in ["high", "critical"]:
            performance_metrics["recommendations"].append({
                "type": "warning",
                "message": "Xotira ishlatilishi yuqori darajada. Tizimni monitoring qiling."
            })
        
        if disk_pressure in ["high", "critical"]:
            performance_metrics["recommendations"].append({
                "type": "warning", 
                "message": "Disk bo'sh joyi kam. Eski fayllarni tozalashni ko'rib chiqing."
            })
        
        if not services_status.get("nginx", False):
            performance_metrics["recommendations"].append({
                "type": "error",
                "message": "Nginx service ishlamayapti. Tizimni tekshiring."
            })
        
        if len(all_subdomains) > 1000:
            performance_metrics["recommendations"].append({
                "type": "info",
                "message": "Ko'p subdomenlar mavjud. Performance optimizatsiyasini ko'rib chiqing."
            })
        
        return {"success": True, "performance_metrics": performance_metrics}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance metrics: {str(e)}")