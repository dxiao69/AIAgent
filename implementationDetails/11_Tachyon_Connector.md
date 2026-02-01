# 11 - Tachyon (1E) Connector Implementation Guide

## Overview

This guide covers implementing the Tachyon connector for real-time device queries and instruction execution. Tachyon enables immediate data collection and remediation actions across managed endpoints.

---

## Prerequisites

- Core service API complete (see [04_Core_Service_API.md](04_Core_Service_API.md))
- Tachyon platform with API access
- X.509 certificate for API authentication

---

## Step 1: Tachyon Configuration

📝 **PROMPT: Create Tachyon connector configuration**
```
Create configuration for Tachyon API integration:
- Support certificate-based authentication
- Platform URL and API version settings
- Consumer name and timeout settings
- Instruction namespace configuration
```

**File: `services/tachyon-connector/src/tachyon_connector/config.py`**

```python
"""Tachyon connector configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Tachyon connector settings."""
    
    # Service settings
    service_name: str = "tachyon-connector"
    debug: bool = False
    api_port: int = 8005
    
    # Tachyon platform settings
    tachyon_platform_url: str = "https://tachyon.company.com"
    tachyon_api_version: str = "v1"
    
    # Certificate authentication
    tachyon_cert_path: Optional[str] = None
    tachyon_key_path: Optional[str] = None
    tachyon_ca_bundle_path: Optional[str] = None
    
    # API key authentication (alternative)
    tachyon_api_key: Optional[str] = None
    
    # Consumer settings
    consumer_name: str = "ITOpsAIAgent"
    consumer_version: str = "1.0.0"
    
    # Instruction settings
    default_instruction_namespace: str = "1E-Explorer"
    instruction_timeout: int = 300  # 5 minutes
    response_polling_interval: int = 5  # seconds
    max_response_wait: int = 600  # 10 minutes
    
    # Device settings
    max_devices_per_instruction: int = 10000
    
    @property
    def api_base_url(self) -> str:
        """Get Tachyon API base URL."""
        return f"{self.tachyon_platform_url}/Tachyon/api/{self.tachyon_api_version}"
    
    model_config = {
        "env_file": ".env",
        "env_prefix": "TACHYON_",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## Step 2: Tachyon API Client

📝 **PROMPT: Create Tachyon REST API client**
```
Create a Tachyon API client class that:
- Handles certificate-based authentication
- Executes instructions against devices
- Polls for instruction responses
- Supports various instruction types (query, action)
- Handles device targeting (FQDN, coverage tags)
```

**File: `services/tachyon-connector/src/tachyon_connector/client.py`**

```python
"""Tachyon REST API client."""

import asyncio
import ssl
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from tachyon_connector.config import get_settings

logger = structlog.get_logger()


class InstructionStatus(str, Enum):
    """Instruction execution status."""
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETE = "Complete"
    FAILED = "Failed"
    CANCELLED = "Cancelled"
    TIMEOUT = "Timeout"


class DeviceTarget:
    """Device targeting for instructions."""
    
    def __init__(
        self,
        fqdns: Optional[List[str]] = None,
        coverage_tags: Optional[List[str]] = None,
        device_ids: Optional[List[str]] = None,
        custom_filter: Optional[str] = None,
    ):
        self.fqdns = fqdns
        self.coverage_tags = coverage_tags
        self.device_ids = device_ids
        self.custom_filter = custom_filter
    
    def to_payload(self) -> Dict[str, Any]:
        """Convert to API payload."""
        if self.fqdns:
            return {"Fqdns": self.fqdns}
        elif self.device_ids:
            return {"DeviceIds": self.device_ids}
        elif self.coverage_tags:
            return {"CoverageTags": self.coverage_tags}
        elif self.custom_filter:
            return {"Filter": self.custom_filter}
        else:
            return {}


class TachyonClient:
    """Tachyon REST API client."""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[httpx.AsyncClient] = None
    
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with client certificate."""
        ssl_context = ssl.create_default_context()
        
        if self.settings.tachyon_ca_bundle_path:
            ssl_context.load_verify_locations(
                self.settings.tachyon_ca_bundle_path
            )
        
        if self.settings.tachyon_cert_path and self.settings.tachyon_key_path:
            ssl_context.load_cert_chain(
                certfile=self.settings.tachyon_cert_path,
                keyfile=self.settings.tachyon_key_path,
            )
        
        return ssl_context
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client."""
        if self._client is None:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Tachyon-Consumer": self.settings.consumer_name,
            }
            
            if self.settings.tachyon_api_key:
                headers["X-Tachyon-ApiKey"] = self.settings.tachyon_api_key
            
            ssl_context = None
            if self.settings.tachyon_cert_path:
                ssl_context = self._create_ssl_context()
            
            self._client = httpx.AsyncClient(
                base_url=self.settings.api_base_url,
                headers=headers,
                verify=ssl_context or True,
                timeout=60.0,
            )
        
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make API request."""
        client = await self._get_client()
        
        response = await client.request(
            method=method,
            url=endpoint,
            params=params,
            json=json,
        )
        
        if response.status_code >= 400:
            logger.error(
                "Tachyon API error",
                status=response.status_code,
                body=response.text[:500],
            )
        
        response.raise_for_status()
        return response.json()
    
    # Instruction operations
    async def get_instruction(self, instruction_name: str) -> Dict[str, Any]:
        """Get instruction definition by name."""
        result = await self._request(
            "GET",
            f"/instructions/{instruction_name}",
        )
        return result
    
    async def list_instructions(
        self,
        namespace: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List available instructions."""
        params = {}
        if namespace:
            params["Namespace"] = namespace
        if search:
            params["Search"] = search
        
        result = await self._request(
            "GET",
            "/instructions",
            params=params,
        )
        return result.get("Data", [])
    
    async def execute_instruction(
        self,
        instruction_name: str,
        target: DeviceTarget,
        parameters: Optional[Dict[str, Any]] = None,
        wait_for_completion: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute an instruction against target devices.
        
        Args:
            instruction_name: Name of the instruction
            target: Device targeting
            parameters: Instruction parameters
            wait_for_completion: Whether to wait for results
            
        Returns:
            Instruction execution result
        """
        payload = {
            "InstructionName": instruction_name,
            **target.to_payload(),
        }
        
        if parameters:
            payload["Parameters"] = parameters
        
        result = await self._request(
            "POST",
            "/instructions/execute",
            json=payload,
        )
        
        instruction_id = result.get("InstructionId")
        logger.info(
            "Instruction executed",
            instruction_name=instruction_name,
            instruction_id=instruction_id,
        )
        
        if wait_for_completion:
            result = await self.wait_for_instruction(instruction_id)
        
        return result
    
    async def get_instruction_status(
        self,
        instruction_id: str,
    ) -> Dict[str, Any]:
        """Get status of an instruction execution."""
        result = await self._request(
            "GET",
            f"/instructions/executions/{instruction_id}/status",
        )
        return result
    
    async def get_instruction_responses(
        self,
        instruction_id: str,
        offset: int = 0,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Get responses from an instruction execution."""
        result = await self._request(
            "GET",
            f"/instructions/executions/{instruction_id}/responses",
            params={
                "Offset": offset,
                "Limit": limit,
            },
        )
        return result.get("Data", [])
    
    async def wait_for_instruction(
        self,
        instruction_id: str,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Wait for instruction to complete and return results.
        
        Args:
            instruction_id: ID of the instruction execution
            timeout: Max seconds to wait (uses setting default)
            
        Returns:
            Instruction results with status and responses
        """
        timeout = timeout or self.settings.max_response_wait
        poll_interval = self.settings.response_polling_interval
        start_time = datetime.utcnow()
        
        while True:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            
            if elapsed > timeout:
                logger.warning(
                    "Instruction timeout",
                    instruction_id=instruction_id,
                    elapsed=elapsed,
                )
                return {
                    "InstructionId": instruction_id,
                    "Status": InstructionStatus.TIMEOUT,
                    "Responses": [],
                }
            
            status = await self.get_instruction_status(instruction_id)
            state = status.get("State", "")
            
            if state in ["Complete", "Failed", "Cancelled"]:
                responses = await self.get_instruction_responses(instruction_id)
                
                return {
                    "InstructionId": instruction_id,
                    "Status": state,
                    "DeviceCount": status.get("DeviceCount", 0),
                    "ResponseCount": status.get("ResponseCount", 0),
                    "Responses": responses,
                }
            
            await asyncio.sleep(poll_interval)
    
    async def cancel_instruction(self, instruction_id: str) -> bool:
        """Cancel an instruction execution."""
        try:
            await self._request(
                "POST",
                f"/instructions/executions/{instruction_id}/cancel",
            )
            return True
        except Exception as e:
            logger.error(f"Failed to cancel instruction: {e}")
            return False
    
    # Device operations
    async def get_devices(
        self,
        fqdns: Optional[List[str]] = None,
        coverage_tags: Optional[List[str]] = None,
        online_only: bool = False,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get device information."""
        params = {"Limit": limit}
        
        if online_only:
            params["OnlineOnly"] = "true"
        
        if fqdns:
            params["Fqdns"] = ",".join(fqdns)
        
        if coverage_tags:
            params["CoverageTags"] = ",".join(coverage_tags)
        
        result = await self._request(
            "GET",
            "/devices",
            params=params,
        )
        
        return result.get("Data", [])
    
    async def get_device(self, fqdn: str) -> Optional[Dict[str, Any]]:
        """Get single device by FQDN."""
        devices = await self.get_devices(fqdns=[fqdn], limit=1)
        return devices[0] if devices else None


# Common instructions
class CommonInstructions:
    """Commonly used instruction names."""
    
    # System information
    GET_BASIC_INVENTORY = "1E-Explorer-GetBasicInventory"
    GET_DISK_SPACE = "1E-Explorer-GetDiskSpace"
    GET_INSTALLED_SOFTWARE = "1E-Explorer-GetInstalledSoftware"
    GET_SERVICES = "1E-Explorer-GetServices"
    GET_PROCESSES = "1E-Explorer-GetProcesses"
    GET_LOGGED_ON_USERS = "1E-Explorer-GetLoggedOnUsers"
    
    # Actions
    RESTART_SERVICE = "1E-Explorer-RestartService"
    STOP_SERVICE = "1E-Explorer-StopService"
    START_SERVICE = "1E-Explorer-StartService"
    CLEAR_TEMP_FILES = "1E-Explorer-ClearTempFiles"
    
    # Custom (define your own)
    GET_COMPLIANCE_STATUS = "Custom-GetComplianceStatus"


# Singleton instance
_client: Optional[TachyonClient] = None


def get_tachyon_client() -> TachyonClient:
    """Get Tachyon client singleton."""
    global _client
    if _client is None:
        _client = TachyonClient()
    return _client
```

---

## Step 3: Tachyon Service Layer

📝 **PROMPT: Create Tachyon service for device operations**
```
Create a service layer for Tachyon operations that:
- Provides high-level methods for common queries
- Handles result parsing and normalization
- Supports batch operations on multiple devices
- Implements remediation actions
```

**File: `services/tachyon-connector/src/tachyon_connector/services/device_service.py`**

```python
"""Tachyon device service."""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import structlog

from tachyon_connector.client import (
    get_tachyon_client,
    DeviceTarget,
    CommonInstructions,
    InstructionStatus,
)

logger = structlog.get_logger()


@dataclass
class DiskSpaceInfo:
    """Disk space information."""
    fqdn: str
    drive: str
    total_gb: float
    free_gb: float
    free_percent: float


@dataclass
class ServiceInfo:
    """Service information."""
    fqdn: str
    name: str
    display_name: str
    status: str
    start_type: str


@dataclass
class SoftwareInfo:
    """Installed software information."""
    fqdn: str
    name: str
    version: str
    publisher: Optional[str]
    install_date: Optional[str]


class TachyonService:
    """High-level Tachyon operations service."""
    
    def __init__(self):
        self.client = get_tachyon_client()
    
    async def get_disk_space(
        self,
        devices: List[str],
    ) -> List[DiskSpaceInfo]:
        """
        Get disk space information from devices.
        
        Args:
            devices: List of FQDNs
            
        Returns:
            List of DiskSpaceInfo objects
        """
        target = DeviceTarget(fqdns=devices)
        
        result = await self.client.execute_instruction(
            CommonInstructions.GET_DISK_SPACE,
            target=target,
        )
        
        disk_info = []
        
        if result.get("Status") == InstructionStatus.COMPLETE:
            for response in result.get("Responses", []):
                fqdn = response.get("Fqdn", "")
                
                for row in response.get("Rows", []):
                    disk_info.append(DiskSpaceInfo(
                        fqdn=fqdn,
                        drive=row.get("Drive", ""),
                        total_gb=float(row.get("TotalGB", 0)),
                        free_gb=float(row.get("FreeGB", 0)),
                        free_percent=float(row.get("FreePercent", 0)),
                    ))
        
        return disk_info
    
    async def get_services(
        self,
        devices: List[str],
        service_name: Optional[str] = None,
    ) -> List[ServiceInfo]:
        """
        Get service information from devices.
        
        Args:
            devices: List of FQDNs
            service_name: Optional service name filter
            
        Returns:
            List of ServiceInfo objects
        """
        target = DeviceTarget(fqdns=devices)
        
        params = {}
        if service_name:
            params["ServiceName"] = service_name
        
        result = await self.client.execute_instruction(
            CommonInstructions.GET_SERVICES,
            target=target,
            parameters=params,
        )
        
        services = []
        
        if result.get("Status") == InstructionStatus.COMPLETE:
            for response in result.get("Responses", []):
                fqdn = response.get("Fqdn", "")
                
                for row in response.get("Rows", []):
                    services.append(ServiceInfo(
                        fqdn=fqdn,
                        name=row.get("Name", ""),
                        display_name=row.get("DisplayName", ""),
                        status=row.get("Status", ""),
                        start_type=row.get("StartType", ""),
                    ))
        
        return services
    
    async def get_installed_software(
        self,
        devices: List[str],
        software_name: Optional[str] = None,
    ) -> List[SoftwareInfo]:
        """
        Get installed software from devices.
        
        Args:
            devices: List of FQDNs
            software_name: Optional software name filter
            
        Returns:
            List of SoftwareInfo objects
        """
        target = DeviceTarget(fqdns=devices)
        
        params = {}
        if software_name:
            params["SoftwareName"] = software_name
        
        result = await self.client.execute_instruction(
            CommonInstructions.GET_INSTALLED_SOFTWARE,
            target=target,
            parameters=params,
        )
        
        software = []
        
        if result.get("Status") == InstructionStatus.COMPLETE:
            for response in result.get("Responses", []):
                fqdn = response.get("Fqdn", "")
                
                for row in response.get("Rows", []):
                    software.append(SoftwareInfo(
                        fqdn=fqdn,
                        name=row.get("Name", ""),
                        version=row.get("Version", ""),
                        publisher=row.get("Publisher"),
                        install_date=row.get("InstallDate"),
                    ))
        
        return software
    
    async def check_device_online(self, fqdn: str) -> bool:
        """Check if a device is online."""
        device = await self.client.get_device(fqdn)
        return device is not None and device.get("Online", False)
    
    async def restart_service(
        self,
        devices: List[str],
        service_name: str,
    ) -> Dict[str, bool]:
        """
        Restart a service on devices.
        
        Args:
            devices: List of FQDNs
            service_name: Name of service to restart
            
        Returns:
            Dict mapping FQDN to success status
        """
        target = DeviceTarget(fqdns=devices)
        
        result = await self.client.execute_instruction(
            CommonInstructions.RESTART_SERVICE,
            target=target,
            parameters={"ServiceName": service_name},
        )
        
        results = {}
        
        for response in result.get("Responses", []):
            fqdn = response.get("Fqdn", "")
            success = response.get("Status") == "Success"
            results[fqdn] = success
            
            if success:
                logger.info(
                    "Service restarted",
                    fqdn=fqdn,
                    service=service_name,
                )
            else:
                logger.warning(
                    "Service restart failed",
                    fqdn=fqdn,
                    service=service_name,
                    error=response.get("ErrorMessage"),
                )
        
        return results
    
    async def clear_temp_files(
        self,
        devices: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Clear temporary files on devices.
        
        Args:
            devices: List of FQDNs
            
        Returns:
            Dict mapping FQDN to cleanup results
        """
        target = DeviceTarget(fqdns=devices)
        
        result = await self.client.execute_instruction(
            CommonInstructions.CLEAR_TEMP_FILES,
            target=target,
        )
        
        results = {}
        
        for response in result.get("Responses", []):
            fqdn = response.get("Fqdn", "")
            rows = response.get("Rows", [])
            
            if rows:
                results[fqdn] = {
                    "files_deleted": rows[0].get("FilesDeleted", 0),
                    "space_recovered_mb": rows[0].get("SpaceRecoveredMB", 0),
                    "success": True,
                }
            else:
                results[fqdn] = {
                    "success": False,
                    "error": response.get("ErrorMessage", "No response"),
                }
        
        return results
    
    async def execute_custom_instruction(
        self,
        instruction_name: str,
        devices: List[str],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a custom instruction.
        
        Args:
            instruction_name: Name of the instruction
            devices: List of FQDNs
            parameters: Instruction parameters
            
        Returns:
            Raw instruction result
        """
        target = DeviceTarget(fqdns=devices)
        
        result = await self.client.execute_instruction(
            instruction_name,
            target=target,
            parameters=parameters,
        )
        
        return result
```

---

## Step 4: API Routes

**File: `services/tachyon-connector/src/tachyon_connector/routes.py`**

```python
"""Tachyon connector API routes."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from tachyon_connector.client import (
    get_tachyon_client,
    DeviceTarget,
    InstructionStatus,
)
from tachyon_connector.services.device_service import TachyonService


router = APIRouter(prefix="/api", tags=["Tachyon"])


class ExecuteInstructionRequest(BaseModel):
    """Request to execute an instruction."""
    instruction_name: str
    fqdns: Optional[List[str]] = None
    coverage_tags: Optional[List[str]] = None
    device_ids: Optional[List[str]] = None
    custom_filter: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    wait_for_completion: bool = True


class RestartServiceRequest(BaseModel):
    """Request to restart a service."""
    devices: List[str] = Field(..., min_items=1)
    service_name: str


class ClearTempFilesRequest(BaseModel):
    """Request to clear temp files."""
    devices: List[str] = Field(..., min_items=1)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    client = get_tachyon_client()
    try:
        # Try to list instructions
        await client.list_instructions(limit=1)
        return {"status": "healthy", "service": "tachyon"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# Instruction endpoints
@router.get("/instructions")
async def list_instructions(
    namespace: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """List available instructions."""
    client = get_tachyon_client()
    instructions = await client.list_instructions(namespace=namespace, search=search)
    return {"items": instructions, "count": len(instructions)}


@router.get("/instructions/{name}")
async def get_instruction(name: str):
    """Get instruction definition."""
    client = get_tachyon_client()
    
    try:
        instruction = await client.get_instruction(name)
        return instruction
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Instruction not found: {e}")


@router.post("/instructions/execute")
async def execute_instruction(request: ExecuteInstructionRequest):
    """Execute an instruction against target devices."""
    client = get_tachyon_client()
    
    target = DeviceTarget(
        fqdns=request.fqdns,
        coverage_tags=request.coverage_tags,
        device_ids=request.device_ids,
        custom_filter=request.custom_filter,
    )
    
    result = await client.execute_instruction(
        instruction_name=request.instruction_name,
        target=target,
        parameters=request.parameters,
        wait_for_completion=request.wait_for_completion,
    )
    
    return result


@router.get("/instructions/executions/{instruction_id}/status")
async def get_instruction_status(instruction_id: str):
    """Get instruction execution status."""
    client = get_tachyon_client()
    status = await client.get_instruction_status(instruction_id)
    return status


@router.get("/instructions/executions/{instruction_id}/responses")
async def get_instruction_responses(
    instruction_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
):
    """Get instruction execution responses."""
    client = get_tachyon_client()
    responses = await client.get_instruction_responses(
        instruction_id,
        offset=offset,
        limit=limit,
    )
    return {"items": responses, "count": len(responses)}


# Device query endpoints
@router.get("/devices")
async def list_devices(
    fqdns: Optional[str] = Query(None, description="Comma-separated FQDNs"),
    online_only: bool = Query(False),
    limit: int = Query(100, ge=1, le=1000),
):
    """List devices."""
    client = get_tachyon_client()
    
    fqdn_list = fqdns.split(",") if fqdns else None
    
    devices = await client.get_devices(
        fqdns=fqdn_list,
        online_only=online_only,
        limit=limit,
    )
    
    return {"items": devices, "count": len(devices)}


@router.get("/devices/{fqdn}")
async def get_device(fqdn: str):
    """Get device by FQDN."""
    client = get_tachyon_client()
    device = await client.get_device(fqdn)
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return device


@router.get("/devices/{fqdn}/disk-space")
async def get_device_disk_space(fqdn: str):
    """Get disk space for a device."""
    service = TachyonService()
    disk_info = await service.get_disk_space([fqdn])
    return {"items": [d.__dict__ for d in disk_info]}


@router.get("/devices/{fqdn}/services")
async def get_device_services(
    fqdn: str,
    service_name: Optional[str] = Query(None),
):
    """Get services for a device."""
    service = TachyonService()
    services = await service.get_services([fqdn], service_name)
    return {"items": [s.__dict__ for s in services]}


@router.get("/devices/{fqdn}/software")
async def get_device_software(
    fqdn: str,
    name: Optional[str] = Query(None),
):
    """Get installed software for a device."""
    service = TachyonService()
    software = await service.get_installed_software([fqdn], name)
    return {"items": [s.__dict__ for s in software]}


# Action endpoints
@router.post("/actions/restart-service")
async def restart_service(request: RestartServiceRequest):
    """Restart a service on devices."""
    service = TachyonService()
    
    results = await service.restart_service(
        devices=request.devices,
        service_name=request.service_name,
    )
    
    success_count = sum(1 for v in results.values() if v)
    
    return {
        "results": results,
        "success_count": success_count,
        "total_count": len(results),
    }


@router.post("/actions/clear-temp-files")
async def clear_temp_files(request: ClearTempFilesRequest):
    """Clear temporary files on devices."""
    service = TachyonService()
    
    results = await service.clear_temp_files(devices=request.devices)
    
    return {"results": results}


@router.post("/actions/custom")
async def execute_custom_action(
    instruction_name: str,
    devices: List[str],
    parameters: Optional[Dict[str, Any]] = None,
):
    """Execute a custom action instruction."""
    service = TachyonService()
    
    result = await service.execute_custom_instruction(
        instruction_name=instruction_name,
        devices=devices,
        parameters=parameters,
    )
    
    return result
```

---

## Step 5: Main Application

**File: `services/tachyon-connector/src/tachyon_connector/main.py`**

```python
"""Tachyon connector FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tachyon_connector.config import get_settings
from tachyon_connector.client import get_tachyon_client
from tachyon_connector.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle."""
    yield
    # Cleanup
    client = get_tachyon_client()
    await client.close()


def create_app() -> FastAPI:
    """Create FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="Tachyon Connector",
        description="Connector for 1E Tachyon integration",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(router)
    
    return app


app = create_app()
```

---

## Step 6: Integration with Action Worker

📝 **PROMPT: Create Tachyon action handler**
```
Create an action handler that integrates with the action worker:
- Executes Tachyon instructions based on action type
- Maps action parameters to instruction parameters
- Reports results back to the core service
```

**File: `services/tachyon-connector/src/tachyon_connector/actions.py`**

```python
"""Tachyon action handlers for action worker integration."""

from typing import Any, Dict, List

import structlog

from tachyon_connector.services.device_service import TachyonService
from tachyon_connector.client import CommonInstructions

logger = structlog.get_logger()


class TachyonActionHandler:
    """Handler for Tachyon-based remediation actions."""
    
    def __init__(self):
        self.service = TachyonService()
    
    async def execute_action(
        self,
        action_type: str,
        devices: List[str],
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a Tachyon action.
        
        Args:
            action_type: Type of action to execute
            devices: Target device FQDNs
            parameters: Action parameters
            
        Returns:
            Action execution result
        """
        handler_map = {
            "restart_service": self._handle_restart_service,
            "clear_temp_files": self._handle_clear_temp_files,
            "collect_disk_space": self._handle_collect_disk_space,
            "collect_software": self._handle_collect_software,
            "custom_instruction": self._handle_custom_instruction,
        }
        
        handler = handler_map.get(action_type)
        
        if not handler:
            return {
                "success": False,
                "error": f"Unknown action type: {action_type}",
            }
        
        try:
            result = await handler(devices, parameters)
            return {
                "success": True,
                "result": result,
            }
        except Exception as e:
            logger.exception("Action execution failed", action_type=action_type)
            return {
                "success": False,
                "error": str(e),
            }
    
    async def _handle_restart_service(
        self,
        devices: List[str],
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle restart service action."""
        service_name = parameters.get("service_name")
        if not service_name:
            raise ValueError("service_name parameter required")
        
        results = await self.service.restart_service(devices, service_name)
        
        return {
            "action": "restart_service",
            "service_name": service_name,
            "device_results": results,
            "success_count": sum(1 for v in results.values() if v),
        }
    
    async def _handle_clear_temp_files(
        self,
        devices: List[str],
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle clear temp files action."""
        results = await self.service.clear_temp_files(devices)
        
        total_recovered = sum(
            r.get("space_recovered_mb", 0)
            for r in results.values()
            if r.get("success")
        )
        
        return {
            "action": "clear_temp_files",
            "device_results": results,
            "total_space_recovered_mb": total_recovered,
        }
    
    async def _handle_collect_disk_space(
        self,
        devices: List[str],
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle collect disk space action."""
        disk_info = await self.service.get_disk_space(devices)
        
        return {
            "action": "collect_disk_space",
            "device_count": len(devices),
            "disk_info": [d.__dict__ for d in disk_info],
        }
    
    async def _handle_collect_software(
        self,
        devices: List[str],
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle collect software action."""
        software_name = parameters.get("software_name")
        software = await self.service.get_installed_software(devices, software_name)
        
        return {
            "action": "collect_software",
            "device_count": len(devices),
            "software_count": len(software),
            "software": [s.__dict__ for s in software],
        }
    
    async def _handle_custom_instruction(
        self,
        devices: List[str],
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle custom instruction action."""
        instruction_name = parameters.get("instruction_name")
        instruction_params = parameters.get("instruction_parameters", {})
        
        if not instruction_name:
            raise ValueError("instruction_name parameter required")
        
        result = await self.service.execute_custom_instruction(
            instruction_name=instruction_name,
            devices=devices,
            parameters=instruction_params,
        )
        
        return {
            "action": "custom_instruction",
            "instruction_name": instruction_name,
            "result": result,
        }
```

---

## Verification

### Test Tachyon Connection

```powershell
# Set environment variables
$env:TACHYON_PLATFORM_URL = "https://tachyon.company.com"
$env:TACHYON_CERT_PATH = "C:\certs\client.pem"
$env:TACHYON_KEY_PATH = "C:\certs\client-key.pem"

# Start service
cd services/tachyon-connector
uvicorn tachyon_connector.main:app --reload --port 8005

# Test health
curl http://localhost:8005/api/health

# List available instructions
curl http://localhost:8005/api/instructions

# Get disk space for a device
curl http://localhost:8005/api/devices/DESKTOP-001.company.com/disk-space
```

---

## Common Issues

### Issue: Certificate authentication fails

**Solution:** Ensure certificate is valid and properly formatted (PEM). Verify certificate is registered in Tachyon.

### Issue: Instruction timeout

**Solution:** Increase `max_response_wait` setting. Check if target devices are online.

### Issue: No responses from instruction

**Solution:** Verify target devices have Tachyon agent installed and communicating. Check coverage tags.

---

## Next Steps

→ [12_Action_Worker.md](12_Action_Worker.md) - Implement action execution worker

---

**Checkpoint:** You should now have:
- [ ] Tachyon client connecting successfully
- [ ] Instructions listing from API
- [ ] Device queries working
- [ ] Service restart action functional
- [ ] Disk space collection returning data
