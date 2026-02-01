# 10 - ServiceNow Connector Implementation Guide

## Overview

This guide covers implementing the ServiceNow connector for creating incidents, change requests, and querying CMDB data. This enables the action workflow to create tickets for remediation.

---

## Prerequisites

- Core service API complete (see [04_Core_Service_API.md](04_Core_Service_API.md))
- ServiceNow instance with API access
- ServiceNow credentials (user/password or OAuth)

---

## Step 1: ServiceNow Configuration

📝 **PROMPT: Create ServiceNow connector configuration**
```
Create configuration for ServiceNow API integration:
- Support both Basic Auth and OAuth 2.0
- Instance URL and API version settings
- Default assignment groups and priorities
- Rate limiting settings
```

**File: `services/servicenow-connector/src/servicenow_connector/config.py`**

```python
"""ServiceNow connector configuration."""

from functools import lru_cache
from typing import Optional, List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """ServiceNow connector settings."""
    
    # Service settings
    service_name: str = "servicenow-connector"
    debug: bool = False
    api_port: int = 8004
    
    # ServiceNow instance
    snow_instance_url: str = "https://yourcompany.service-now.com"
    snow_api_version: str = "v2"
    
    # Authentication
    snow_auth_type: str = "basic"  # basic or oauth
    snow_username: Optional[str] = None
    snow_password: Optional[str] = None
    
    # OAuth settings
    snow_client_id: Optional[str] = None
    snow_client_secret: Optional[str] = None
    snow_oauth_token_url: Optional[str] = None
    
    # Default values for tickets
    default_assignment_group: str = "IT Operations"
    default_category: str = "Software"
    default_impact: int = 3  # 1=High, 2=Medium, 3=Low
    default_urgency: int = 3
    
    # Rate limiting
    max_requests_per_minute: int = 60
    request_timeout: int = 30
    
    # Tables
    incident_table: str = "incident"
    change_request_table: str = "change_request"
    cmdb_ci_table: str = "cmdb_ci"
    cmdb_ci_computer_table: str = "cmdb_ci_computer"
    
    @property
    def api_base_url(self) -> str:
        """Get ServiceNow API base URL."""
        return f"{self.snow_instance_url}/api/now/{self.snow_api_version}"
    
    model_config = {
        "env_file": ".env",
        "env_prefix": "SNOW_",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## Step 2: ServiceNow API Client

📝 **PROMPT: Create ServiceNow REST API client**
```
Create a ServiceNow API client class that:
- Handles authentication (Basic and OAuth)
- Implements CRUD operations for incidents
- Supports creating change requests
- Queries CMDB for configuration items
- Handles pagination and rate limiting
```

**File: `services/servicenow-connector/src/servicenow_connector/client.py`**

```python
"""ServiceNow REST API client."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from servicenow_connector.config import get_settings

logger = structlog.get_logger()


class ServiceNowAuth:
    """Authentication handler for ServiceNow."""
    
    def __init__(self):
        self.settings = get_settings()
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
    
    async def get_auth_header(self) -> Dict[str, str]:
        """Get authentication header."""
        if self.settings.snow_auth_type == "basic":
            import base64
            credentials = f"{self.settings.snow_username}:{self.settings.snow_password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            return {"Authorization": f"Basic {encoded}"}
        
        elif self.settings.snow_auth_type == "oauth":
            token = await self._get_oauth_token()
            return {"Authorization": f"Bearer {token}"}
        
        else:
            raise ValueError(f"Unknown auth type: {self.settings.snow_auth_type}")
    
    async def _get_oauth_token(self) -> str:
        """Get or refresh OAuth token."""
        if self._token and self._token_expiry and datetime.utcnow() < self._token_expiry:
            return self._token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.settings.snow_oauth_token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.settings.snow_client_id,
                    "client_secret": self.settings.snow_client_secret,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            self._token = data["access_token"]
            expires_in = data.get("expires_in", 3600)
            self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 60)
            
            return self._token


class ServiceNowClient:
    """ServiceNow REST API client."""
    
    def __init__(self):
        self.settings = get_settings()
        self.auth = ServiceNowAuth()
        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_time: Optional[datetime] = None
        self._request_count = 0
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client with auth headers."""
        if self._client is None:
            auth_header = await self.auth.get_auth_header()
            self._client = httpx.AsyncClient(
                base_url=self.settings.api_base_url,
                headers={
                    **auth_header,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=self.settings.request_timeout,
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _rate_limit(self):
        """Apply rate limiting."""
        now = datetime.utcnow()
        
        if self._last_request_time:
            elapsed = (now - self._last_request_time).total_seconds()
            
            if elapsed < 60:
                self._request_count += 1
                
                if self._request_count >= self.settings.max_requests_per_minute:
                    sleep_time = 60 - elapsed
                    logger.warning(f"Rate limit reached, sleeping {sleep_time:.1f}s")
                    await asyncio.sleep(sleep_time)
                    self._request_count = 0
            else:
                self._request_count = 0
        
        self._last_request_time = now
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make API request with retry logic."""
        await self._rate_limit()
        
        client = await self._get_client()
        
        response = await client.request(
            method=method,
            url=endpoint,
            params=params,
            json=json,
        )
        
        if response.status_code >= 400:
            logger.error(
                "ServiceNow API error",
                status=response.status_code,
                body=response.text,
            )
        
        response.raise_for_status()
        return response.json()
    
    # Incident operations
    async def create_incident(
        self,
        short_description: str,
        description: str,
        caller_id: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        impact: Optional[int] = None,
        urgency: Optional[int] = None,
        assignment_group: Optional[str] = None,
        cmdb_ci: Optional[str] = None,
        additional_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new incident.
        
        Returns the created incident record.
        """
        payload = {
            "short_description": short_description,
            "description": description,
            "category": category or self.settings.default_category,
            "impact": impact or self.settings.default_impact,
            "urgency": urgency or self.settings.default_urgency,
            "assignment_group": assignment_group or self.settings.default_assignment_group,
        }
        
        if caller_id:
            payload["caller_id"] = caller_id
        
        if subcategory:
            payload["subcategory"] = subcategory
        
        if cmdb_ci:
            payload["cmdb_ci"] = cmdb_ci
        
        if additional_fields:
            payload.update(additional_fields)
        
        result = await self._request(
            "POST",
            f"/table/{self.settings.incident_table}",
            json=payload,
        )
        
        logger.info(
            "Incident created",
            number=result.get("result", {}).get("number"),
            sys_id=result.get("result", {}).get("sys_id"),
        )
        
        return result.get("result", {})
    
    async def get_incident(self, sys_id: str) -> Dict[str, Any]:
        """Get incident by sys_id."""
        result = await self._request(
            "GET",
            f"/table/{self.settings.incident_table}/{sys_id}",
        )
        return result.get("result", {})
    
    async def update_incident(
        self,
        sys_id: str,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update an incident."""
        result = await self._request(
            "PATCH",
            f"/table/{self.settings.incident_table}/{sys_id}",
            json=updates,
        )
        return result.get("result", {})
    
    async def close_incident(
        self,
        sys_id: str,
        close_code: str,
        close_notes: str,
    ) -> Dict[str, Any]:
        """Close an incident."""
        return await self.update_incident(
            sys_id,
            {
                "state": "7",  # Closed
                "close_code": close_code,
                "close_notes": close_notes,
            },
        )
    
    async def list_incidents(
        self,
        query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """List incidents with optional filtering."""
        params = {
            "sysparm_limit": limit,
            "sysparm_offset": offset,
        }
        
        if query:
            params["sysparm_query"] = query
        
        if fields:
            params["sysparm_fields"] = ",".join(fields)
        
        result = await self._request(
            "GET",
            f"/table/{self.settings.incident_table}",
            params=params,
        )
        
        return result.get("result", [])
    
    # Change Request operations
    async def create_change_request(
        self,
        short_description: str,
        description: str,
        type: str = "normal",  # normal, standard, emergency
        category: Optional[str] = None,
        assignment_group: Optional[str] = None,
        cmdb_ci: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        additional_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a change request."""
        payload = {
            "short_description": short_description,
            "description": description,
            "type": type,
            "assignment_group": assignment_group or self.settings.default_assignment_group,
        }
        
        if category:
            payload["category"] = category
        
        if cmdb_ci:
            payload["cmdb_ci"] = cmdb_ci
        
        if start_date:
            payload["start_date"] = start_date
        
        if end_date:
            payload["end_date"] = end_date
        
        if additional_fields:
            payload.update(additional_fields)
        
        result = await self._request(
            "POST",
            f"/table/{self.settings.change_request_table}",
            json=payload,
        )
        
        return result.get("result", {})
    
    # CMDB operations
    async def get_ci_by_name(
        self,
        name: str,
        ci_class: str = "cmdb_ci_computer",
    ) -> Optional[Dict[str, Any]]:
        """Get CMDB CI by name."""
        result = await self._request(
            "GET",
            f"/table/{ci_class}",
            params={
                "sysparm_query": f"name={name}",
                "sysparm_limit": 1,
            },
        )
        
        items = result.get("result", [])
        return items[0] if items else None
    
    async def list_cis(
        self,
        query: Optional[str] = None,
        ci_class: str = "cmdb_ci_computer",
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List CMDB configuration items."""
        params = {
            "sysparm_limit": limit,
            "sysparm_offset": offset,
        }
        
        if query:
            params["sysparm_query"] = query
        
        result = await self._request(
            "GET",
            f"/table/{ci_class}",
            params=params,
        )
        
        return result.get("result", [])
    
    async def update_ci(
        self,
        sys_id: str,
        updates: Dict[str, Any],
        ci_class: str = "cmdb_ci_computer",
    ) -> Dict[str, Any]:
        """Update a CMDB CI."""
        result = await self._request(
            "PATCH",
            f"/table/{ci_class}/{sys_id}",
            json=updates,
        )
        return result.get("result", {})


# Singleton instance
_client: Optional[ServiceNowClient] = None


def get_servicenow_client() -> ServiceNowClient:
    """Get ServiceNow client singleton."""
    global _client
    if _client is None:
        _client = ServiceNowClient()
    return _client
```

---

## Step 3: Incident Service

📝 **PROMPT: Create incident management service**
```
Create a service layer for incident management that:
- Creates incidents from scan results
- Groups multiple issues into single incidents
- Tracks incident status
- Provides templates for common issue types
```

**File: `services/servicenow-connector/src/servicenow_connector/services/incidents.py`**

```python
"""Incident management service."""

from typing import Any, Dict, List, Optional
from datetime import datetime

import structlog

from servicenow_connector.client import get_servicenow_client
from servicenow_connector.config import get_settings

logger = structlog.get_logger()


class IncidentTemplates:
    """Templates for common incident types."""
    
    LOW_DISK_SPACE = {
        "category": "Hardware",
        "subcategory": "Storage",
        "short_description_template": "Low disk space on {device_count} device(s)",
        "description_template": """
Automated alert from IT Operations AI Agent.

Issue: Low disk space detected on the following device(s):

{device_list}

Recommended Actions:
1. Review and clean up temporary files
2. Archive or delete unnecessary data
3. Consider storage expansion if recurring

Scan Details:
- Rule: {rule_name}
- Scan ID: {scan_id}
- Scan Time: {scan_time}
""",
        "impact": 2,
        "urgency": 2,
    }
    
    MISSING_PATCHES = {
        "category": "Software",
        "subcategory": "Patching",
        "short_description_template": "Missing critical patches on {device_count} device(s)",
        "description_template": """
Automated alert from IT Operations AI Agent.

Issue: Critical security patches missing on the following device(s):

{device_list}

Missing Patches Summary:
{patch_summary}

Recommended Actions:
1. Schedule patching maintenance window
2. Test patches in staging environment
3. Deploy patches via MECM

Scan Details:
- Rule: {rule_name}
- Scan ID: {scan_id}
- Scan Time: {scan_time}
""",
        "impact": 1,
        "urgency": 1,
    }
    
    INACTIVE_DEVICES = {
        "category": "Hardware",
        "subcategory": "Asset Management",
        "short_description_template": "{device_count} device(s) inactive for extended period",
        "description_template": """
Automated alert from IT Operations AI Agent.

Issue: The following device(s) have been inactive for an extended period:

{device_list}

Recommended Actions:
1. Verify device physical status
2. Check for hardware issues
3. Update asset management records
4. Consider decommissioning if no longer needed

Scan Details:
- Rule: {rule_name}
- Scan ID: {scan_id}
- Scan Time: {scan_time}
""",
        "impact": 3,
        "urgency": 3,
    }
    
    VULNERABLE_SOFTWARE = {
        "category": "Software",
        "subcategory": "Security",
        "short_description_template": "Vulnerable software detected: {app_name}",
        "description_template": """
Automated alert from IT Operations AI Agent.

Issue: Vulnerable software detected across {install_count} installation(s):

Application: {app_name}
Version: {app_version}
Publisher: {publisher}
CVE Count: {cve_count}

Affected Devices:
{device_list}

Recommended Actions:
1. Update to latest secure version
2. If update unavailable, consider alternative software
3. Implement compensating controls if removal not possible

Scan Details:
- Rule: {rule_name}
- Scan ID: {scan_id}
- Scan Time: {scan_time}
""",
        "impact": 1,
        "urgency": 2,
    }


class IncidentService:
    """Service for creating and managing incidents."""
    
    def __init__(self):
        self.client = get_servicenow_client()
        self.settings = get_settings()
        self.templates = IncidentTemplates()
    
    async def create_incident_from_scan(
        self,
        scan_results: Dict[str, Any],
        rule_name: str,
        scan_id: str,
        template_name: str = None,
    ) -> Dict[str, Any]:
        """
        Create an incident from scan results.
        
        Args:
            scan_results: Results from the scan
            rule_name: Name of the rule that was executed
            scan_id: ID of the scan
            template_name: Optional template to use
            
        Returns:
            Created incident details
        """
        # Determine template based on results or explicit name
        template = self._get_template(template_name, scan_results)
        
        # Prepare device list
        results = scan_results.get("results", [])
        device_list = self._format_device_list(results)
        
        # Format description from template
        description = template["description_template"].format(
            device_count=len(results),
            device_list=device_list,
            rule_name=rule_name,
            scan_id=scan_id,
            scan_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            patch_summary=self._format_patch_summary(results),
            app_name=results[0].get("app_name", "N/A") if results else "N/A",
            app_version=results[0].get("app_version", "N/A") if results else "N/A",
            publisher=results[0].get("publisher", "N/A") if results else "N/A",
            cve_count=results[0].get("cve_count", 0) if results else 0,
            install_count=len(results),
        )
        
        short_description = template["short_description_template"].format(
            device_count=len(results),
            app_name=results[0].get("app_name", "N/A") if results else "N/A",
        )
        
        # Look up CMDB CI for first device (if available)
        cmdb_ci = None
        if results and results[0].get("entity_name"):
            ci = await self.client.get_ci_by_name(results[0]["entity_name"])
            if ci:
                cmdb_ci = ci.get("sys_id")
        
        # Create the incident
        incident = await self.client.create_incident(
            short_description=short_description,
            description=description,
            category=template["category"],
            subcategory=template["subcategory"],
            impact=template["impact"],
            urgency=template["urgency"],
            cmdb_ci=cmdb_ci,
            additional_fields={
                "u_scan_id": scan_id,  # Custom field
                "u_rule_name": rule_name,
                "u_device_count": len(results),
            },
        )
        
        logger.info(
            "Incident created from scan",
            incident_number=incident.get("number"),
            device_count=len(results),
            rule_name=rule_name,
        )
        
        return incident
    
    async def create_bulk_incidents(
        self,
        scan_results: Dict[str, Any],
        rule_name: str,
        scan_id: str,
        group_by: str = "severity",
        max_devices_per_incident: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Create multiple incidents, grouping results.
        
        Args:
            scan_results: Results from the scan
            rule_name: Name of the rule
            scan_id: Scan ID
            group_by: How to group results (severity, entity_type)
            max_devices_per_incident: Max devices per incident
            
        Returns:
            List of created incidents
        """
        results = scan_results.get("results", [])
        
        # Group results
        groups = {}
        for result in results:
            key = result.get(group_by, "default")
            if key not in groups:
                groups[key] = []
            groups[key].append(result)
        
        incidents = []
        
        for group_key, group_results in groups.items():
            # Split large groups
            chunks = [
                group_results[i:i + max_devices_per_incident]
                for i in range(0, len(group_results), max_devices_per_incident)
            ]
            
            for chunk in chunks:
                incident = await self.create_incident_from_scan(
                    scan_results={"results": chunk},
                    rule_name=f"{rule_name} ({group_key})",
                    scan_id=scan_id,
                )
                incidents.append(incident)
        
        return incidents
    
    async def get_related_incidents(
        self,
        device_name: str,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get recent incidents related to a device."""
        query = f"descriptionLIKE{device_name}^sys_created_on>=javascript:gs.daysAgo({days})"
        
        incidents = await self.client.list_incidents(
            query=query,
            fields=["number", "short_description", "state", "sys_created_on"],
        )
        
        return incidents
    
    def _get_template(
        self,
        template_name: Optional[str],
        scan_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Get appropriate template."""
        if template_name:
            return getattr(self.templates, template_name, self.templates.LOW_DISK_SPACE)
        
        # Auto-detect based on results
        results = scan_results.get("results", [])
        if not results:
            return self.templates.LOW_DISK_SPACE
        
        # Check matched conditions
        conditions = results[0].get("matched_conditions", [])
        
        if any("disk" in c.lower() for c in conditions):
            return self.templates.LOW_DISK_SPACE
        elif any("patch" in c.lower() for c in conditions):
            return self.templates.MISSING_PATCHES
        elif any("inactive" in c.lower() or "active" in c.lower() for c in conditions):
            return self.templates.INACTIVE_DEVICES
        elif any("cve" in c.lower() or "vulnerab" in c.lower() for c in conditions):
            return self.templates.VULNERABLE_SOFTWARE
        
        return self.templates.LOW_DISK_SPACE
    
    def _format_device_list(self, results: List[Dict[str, Any]]) -> str:
        """Format device list for incident description."""
        lines = []
        for r in results[:20]:  # Limit to 20 devices
            name = r.get("entity_name", "Unknown")
            severity = r.get("severity", "medium")
            details = r.get("details", {})
            
            detail_str = ", ".join(f"{k}={v}" for k, v in list(details.items())[:3])
            lines.append(f"- {name} [{severity}]: {detail_str}")
        
        if len(results) > 20:
            lines.append(f"... and {len(results) - 20} more device(s)")
        
        return "\n".join(lines)
    
    def _format_patch_summary(self, results: List[Dict[str, Any]]) -> str:
        """Format patch summary for incident description."""
        patch_counts = {}
        for r in results:
            details = r.get("details", {})
            missing = details.get("missing_critical_patches", 0)
            if missing > 0:
                patch_counts[r.get("entity_name", "Unknown")] = missing
        
        if not patch_counts:
            return "No patch details available"
        
        lines = [f"- {name}: {count} critical patches" for name, count in patch_counts.items()]
        return "\n".join(lines[:10])
```

---

## Step 4: API Routes

**File: `services/servicenow-connector/src/servicenow_connector/routes.py`**

```python
"""ServiceNow connector API routes."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from servicenow_connector.client import get_servicenow_client
from servicenow_connector.services.incidents import IncidentService


router = APIRouter(prefix="/api", tags=["ServiceNow"])


class CreateIncidentRequest(BaseModel):
    """Request to create an incident."""
    short_description: str = Field(..., min_length=10)
    description: str = Field(..., min_length=20)
    category: Optional[str] = None
    subcategory: Optional[str] = None
    impact: Optional[int] = Field(None, ge=1, le=3)
    urgency: Optional[int] = Field(None, ge=1, le=3)
    assignment_group: Optional[str] = None
    cmdb_ci: Optional[str] = None


class CreateIncidentFromScanRequest(BaseModel):
    """Request to create incident from scan results."""
    scan_results: Dict[str, Any]
    rule_name: str
    scan_id: str
    template_name: Optional[str] = None


class CreateChangeRequest(BaseModel):
    """Request to create a change request."""
    short_description: str
    description: str
    type: str = "normal"
    category: Optional[str] = None
    assignment_group: Optional[str] = None
    cmdb_ci: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class IncidentResponse(BaseModel):
    """Incident response."""
    sys_id: str
    number: str
    short_description: str
    state: str
    priority: Optional[str] = None


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    client = get_servicenow_client()
    try:
        # Try to list one incident to verify connectivity
        await client.list_incidents(limit=1)
        return {"status": "healthy", "service": "servicenow"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# Incident endpoints
@router.post("/incidents", response_model=IncidentResponse)
async def create_incident(request: CreateIncidentRequest):
    """Create a new incident."""
    client = get_servicenow_client()
    
    try:
        incident = await client.create_incident(
            short_description=request.short_description,
            description=request.description,
            category=request.category,
            subcategory=request.subcategory,
            impact=request.impact,
            urgency=request.urgency,
            assignment_group=request.assignment_group,
            cmdb_ci=request.cmdb_ci,
        )
        
        return IncidentResponse(
            sys_id=incident["sys_id"],
            number=incident["number"],
            short_description=incident["short_description"],
            state=incident.get("state", "1"),
            priority=incident.get("priority"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/incidents/from-scan")
async def create_incident_from_scan(request: CreateIncidentFromScanRequest):
    """Create incident from scan results."""
    service = IncidentService()
    
    try:
        incident = await service.create_incident_from_scan(
            scan_results=request.scan_results,
            rule_name=request.rule_name,
            scan_id=request.scan_id,
            template_name=request.template_name,
        )
        
        return {
            "sys_id": incident["sys_id"],
            "number": incident["number"],
            "short_description": incident["short_description"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/incidents/{sys_id}")
async def get_incident(sys_id: str):
    """Get incident by sys_id."""
    client = get_servicenow_client()
    
    incident = await client.get_incident(sys_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return incident


@router.patch("/incidents/{sys_id}")
async def update_incident(sys_id: str, updates: Dict[str, Any]):
    """Update an incident."""
    client = get_servicenow_client()
    
    incident = await client.update_incident(sys_id, updates)
    return incident


@router.get("/incidents")
async def list_incidents(
    query: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List incidents."""
    client = get_servicenow_client()
    
    incidents = await client.list_incidents(
        query=query,
        limit=limit,
        offset=offset,
    )
    
    return {"items": incidents, "count": len(incidents)}


# Change Request endpoints
@router.post("/changes")
async def create_change_request(request: CreateChangeRequest):
    """Create a change request."""
    client = get_servicenow_client()
    
    try:
        change = await client.create_change_request(
            short_description=request.short_description,
            description=request.description,
            type=request.type,
            category=request.category,
            assignment_group=request.assignment_group,
            cmdb_ci=request.cmdb_ci,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        
        return {
            "sys_id": change["sys_id"],
            "number": change["number"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# CMDB endpoints
@router.get("/cmdb/ci/{name}")
async def get_ci_by_name(name: str, ci_class: str = "cmdb_ci_computer"):
    """Get CMDB CI by name."""
    client = get_servicenow_client()
    
    ci = await client.get_ci_by_name(name, ci_class)
    if not ci:
        raise HTTPException(status_code=404, detail="CI not found")
    
    return ci


@router.get("/cmdb/ci")
async def list_cis(
    query: Optional[str] = Query(None),
    ci_class: str = Query("cmdb_ci_computer"),
    limit: int = Query(100, ge=1, le=500),
):
    """List CMDB CIs."""
    client = get_servicenow_client()
    
    cis = await client.list_cis(query=query, ci_class=ci_class, limit=limit)
    return {"items": cis, "count": len(cis)}
```

---

## Step 5: Main Application

**File: `services/servicenow-connector/src/servicenow_connector/main.py`**

```python
"""ServiceNow connector FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from servicenow_connector.config import get_settings
from servicenow_connector.client import get_servicenow_client
from servicenow_connector.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle."""
    yield
    # Cleanup
    client = get_servicenow_client()
    await client.close()


def create_app() -> FastAPI:
    """Create FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="ServiceNow Connector",
        description="Connector for ServiceNow ITSM integration",
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

## Verification

### Test ServiceNow Connection

```powershell
# Set environment variables
$env:SNOW_INSTANCE_URL = "https://yourcompany.service-now.com"
$env:SNOW_USERNAME = "api_user"
$env:SNOW_PASSWORD = "password"

# Start service
cd services/servicenow-connector
uvicorn servicenow_connector.main:app --reload --port 8004

# Test health
curl http://localhost:8004/api/health

# Test creating incident
curl -X POST http://localhost:8004/api/incidents `
  -H "Content-Type: application/json" `
  -d '{"short_description": "Test incident from API", "description": "This is a test"}'
```

---

## Common Issues

### Issue: Authentication failures

**Solution:** Verify credentials and ensure API user has correct roles in ServiceNow

### Issue: Rate limiting errors

**Solution:** Reduce max_requests_per_minute or implement request queuing

### Issue: CMDB CI not found

**Solution:** Ensure device names match exactly or use fuzzy matching

---

## Next Steps

→ [11_Tachyon_Connector.md](11_Tachyon_Connector.md) - Implement Tachyon integration

---

**Checkpoint:** You should now have:
- [ ] ServiceNow client connecting successfully
- [ ] Incident creation working
- [ ] Templates generating proper descriptions
- [ ] CMDB lookup functional
- [ ] Rate limiting preventing API throttling
