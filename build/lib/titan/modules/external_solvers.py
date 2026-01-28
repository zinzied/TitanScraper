"""
External Solvers Module
=======================
Interface for third-party captcha solving services.
Supports 2Captcha, CapMonster, Anti-Captcha, etc.
"""

import time
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ExternalSolver:
    """Interface for external captcha solving services."""
    
    def __init__(self, provider: str, api_key: str, **kwargs):
        self.provider = provider.lower()
        self.api_key = api_key
        self.options = kwargs
        
        # Mapping providers to their standard API endpoints
        self.endpoints = {
            "2captcha": "https://2captcha.com",
            "capmonster": "https://api.capmonster.cloud",
            "anticaptcha": "https://api.anti-captcha.com"
        }
        
    def solve_turnstile(self, site_key: str, page_url: str) -> Optional[str]:
        """Solve Cloudflare Turnstile"""
        if self.provider == "2captcha":
            return self._solve_2captcha("turnstile", {"sitekey": site_key, "pageurl": page_url})
        elif self.provider == "capmonster":
            return self._solve_capmonster("TurnstileTaskProxyless", {"websiteURL": page_url, "websiteKey": site_key})
        elif self.provider == "anticaptcha":
             return self._solve_anticaptcha("TurnstileTaskProxyless", {"websiteURL": page_url, "websiteKey": site_key})
        return None

    def solve_recaptcha_v2(self, site_key: str, page_url: str, enterprise: bool = False) -> Optional[str]:
        """Solve reCAPTCHA v2"""
        if self.provider == "2captcha":
            method = "userrecaptcha"
            return self._solve_2captcha(method, {"googlekey": site_key, "pageurl": page_url})
        elif self.provider == "capmonster":
            task_type = "NoCaptchaTaskProxyless"
            return self._solve_capmonster(task_type, {"websiteURL": page_url, "websiteKey": site_key})
        elif self.provider == "anticaptcha":
            task_type = "NoCaptchaTaskProxyless"
            return self._solve_anticaptcha(task_type, {"websiteURL": page_url, "websiteKey": site_key})
        return None

    def _solve_2captcha(self, method: str, params: dict) -> Optional[str]:
        """2Captcha API logic"""
        try:
            base_url = self.endpoints.get("2captcha", "https://2captcha.com")
            data = {
                "key": self.api_key,
                "method": method,
                "json": 1,
                **params
            }
            
            res = requests.post(f"{base_url}/in.php", data=data, timeout=30).json()
            if res.get("status") != 1:
                logger.error(f"2Captcha Submit Error: {res.get('request')}")
                return None
                
            request_id = res.get("request")
            logger.info(f"2Captcha: Challenge submitted (ID: {request_id})")
            
            # Poll
            for _ in range(60): # max 300s
                time.sleep(5)
                res = requests.get(f"{base_url}/res.php", params={
                    "key": self.api_key,
                    "action": "get",
                    "id": request_id,
                    "json": 1
                }, timeout=30).json()
                
                if res.get("status") == 1:
                    return res.get("request")
                
                if res.get("request") == "CAPCHA_NOT_READY":
                    continue
                
                logger.error(f"2Captcha Poll Error: {res.get('request')}")
                break
                
        except Exception as e:
            logger.error(f"2Captcha Exception: {e}")
            
        return None

    def _solve_capmonster(self, task_type: str, task_data: dict) -> Optional[str]:
        """CapMonster API logic"""
        try:
            base_url = self.endpoints.get("capmonster", "https://api.capmonster.cloud")
            
            create_res = requests.post(f"{base_url}/createTask", json={
                "clientKey": self.api_key,
                "task": {
                    "type": task_type,
                    **task_data
                }
            }, timeout=30).json()
            
            if create_res.get("errorId") != 0:
                logger.error(f"CapMonster Create Error: {create_res.get('errorCode')}")
                return None
                
            task_id = create_res.get("taskId")
            logger.info(f"CapMonster: Task created (ID: {task_id})")
            
            for _ in range(60):
                time.sleep(5)
                res = requests.post(f"{base_url}/getTaskResult", json={
                    "clientKey": self.api_key,
                    "taskId": task_id
                }, timeout=30).json()
                
                if res.get("errorId") != 0:
                    logger.error(f"CapMonster Result Error: {res.get('errorCode')}")
                    break
                    
                if res.get("status") == "ready":
                    solution = res.get("solution", {})
                    return solution.get("gRecaptchaResponse") or solution.get("token")
                    
        except Exception as e:
            logger.error(f"CapMonster Exception: {e}")
            
        return None

    def _solve_anticaptcha(self, task_type: str, task_data: dict) -> Optional[str]:
        """Anti-Captcha API logic"""
        try:
            base_url = self.endpoints.get("anticaptcha", "https://api.anti-captcha.com")
            
            create_res = requests.post(f"{base_url}/createTask", json={
                "clientKey": self.api_key,
                "task": {
                    "type": task_type,
                    **task_data
                }
            }, timeout=30).json()
            
            if create_res.get("errorId") != 0:
                logger.error(f"Anti-Captcha Create Error: {create_res.get('errorCode')}")
                return None
                
            task_id = create_res.get("taskId")
            logger.info(f"Anti-Captcha: Task created (ID: {task_id})")
            
            for _ in range(60):
                time.sleep(5)
                res = requests.post(f"{base_url}/getTaskResult", json={
                    "clientKey": self.api_key,
                    "taskId": task_id
                }, timeout=30).json()
                
                if res.get("errorId") != 0:
                    logger.error(f"Anti-Captcha Result Error: {res.get('errorCode')}")
                    break
                    
                if res.get("status") == "ready":
                    solution = res.get("solution", {})
                    return solution.get("gRecaptchaResponse") or solution.get("token")
                    
        except Exception as e:
            logger.error(f"Anti-Captcha Exception: {e}")
            
        return None
