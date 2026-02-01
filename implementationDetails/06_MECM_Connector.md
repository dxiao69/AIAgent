# 06 - MECM Connector Implementation Guide

## Overview

This guide covers implementing the MECM (Microsoft Endpoint Configuration Manager) connector service that queries device inventory, software inventory, and patch compliance data from MECM's SQL Server database.

---

## Prerequisites

- Core service API complete (see [04_Core_Service_API.md](04_Core_Service_API.md))
- Access to MECM SQL Server database
- SQL Server ODBC driver installed
- Database read permissions granted

---

## Step 1: MECM Database Configuration

📝 **PROMPT: Create MECM database connection configuration**
```
Create configuration for connecting to MECM SQL Server database:
- Support Windows Authentication and SQL Authentication
- Connection pooling
- Query timeout settings
- Health check queries
Use pyodbc with async wrapper (aioodbc or similar).
```

**File: `services/mecm-connector/src/mecm_connector/config.py`**

```python
"""MECM Connector configuration."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Service settings
    service_name: str = "mecm-connector"
    debug: bool = False
    log_level: str = "INFO"
    
    # MECM Database
    mecm_server: str = "mecm-db.company.com"
    mecm_database: str = "CM_ABC"  # Site code database
    mecm_use_windows_auth: bool = True
    mecm_username: Optional[str] = None
    mecm_password: Optional[str] = None
    mecm_query_timeout: int = 120
    mecm_connection_timeout: int = 30
    
    # Connection pooling
    pool_size: int = 5
    pool_recycle: int = 3600
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8002
    
    # Cache settings
    cache_ttl_devices: int = 300  # 5 minutes
    cache_ttl_software: int = 600  # 10 minutes
    redis_url: str = "redis://localhost:6379/1"
    
    @property
    def connection_string(self) -> str:
        """Build ODBC connection string."""
        if self.mecm_use_windows_auth:
            return (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.mecm_server};"
                f"DATABASE={self.mecm_database};"
                f"Trusted_Connection=yes;"
            )
        else:
            return (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.mecm_server};"
                f"DATABASE={self.mecm_database};"
                f"UID={self.mecm_username};"
                f"PWD={self.mecm_password};"
            )
    
    model_config = {
        "env_file": ".env",
        "env_prefix": "MECM_",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

---

## Step 2: Database Connection Manager

📝 **PROMPT: Create async SQL Server connection manager**
```
Create a connection manager for MECM SQL Server with:
- Async query execution using aioodbc
- Connection pooling
- Automatic retry on connection failures
- Query result streaming for large datasets
```

**File: `services/mecm-connector/src/mecm_connector/database.py`**

```python
"""MECM database connection management."""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

import aioodbc
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from mecm_connector.config import get_settings

logger = structlog.get_logger()


class MECMDatabase:
    """MECM SQL Server database connection manager."""
    
    def __init__(self):
        self.settings = get_settings()
        self._pool: Optional[aioodbc.Pool] = None
    
    async def initialize(self):
        """Initialize connection pool."""
        logger.info("Initializing MECM database connection pool")
        
        self._pool = await aioodbc.create_pool(
            dsn=self.settings.connection_string,
            minsize=1,
            maxsize=self.settings.pool_size,
            autocommit=True,
        )
        
        # Test connection
        await self.health_check()
        logger.info("MECM database connection pool initialized")
    
    async def close(self):
        """Close connection pool."""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            logger.info("MECM database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[aioodbc.Connection, None]:
        """Get a connection from the pool."""
        if not self._pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self._pool.acquire() as conn:
            yield conn
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a query and return results as list of dicts.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result dictionaries
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                
                # Get column names
                columns = [column[0] for column in cursor.description]
                
                # Fetch all rows
                rows = await cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
    
    async def execute_query_streaming(
        self,
        query: str,
        params: Optional[tuple] = None,
        batch_size: int = 1000,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute a query and stream results.
        
        Yields results in batches to handle large datasets.
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                
                columns = [column[0] for column in cursor.description]
                
                while True:
                    rows = await cursor.fetchmany(batch_size)
                    if not rows:
                        break
                    
                    for row in rows:
                        yield dict(zip(columns, row))
    
    async def execute_scalar(
        self,
        query: str,
        params: Optional[tuple] = None,
    ) -> Any:
        """Execute query and return single scalar value."""
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                row = await cursor.fetchone()
                return row[0] if row else None
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            result = await self.execute_scalar("SELECT 1")
            return result == 1
        except Exception as e:
            logger.error("MECM database health check failed", error=str(e))
            return False


# Singleton instance
_db_instance: Optional[MECMDatabase] = None


async def get_mecm_db() -> MECMDatabase:
    """Get MECM database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = MECMDatabase()
        await _db_instance.initialize()
    return _db_instance


async def close_mecm_db():
    """Close MECM database connection."""
    global _db_instance
    if _db_instance:
        await _db_instance.close()
        _db_instance = None
```

---

## Step 3: MECM Query Definitions

📝 **PROMPT: Create MECM SQL queries for device and software inventory**
```
Create SQL query definitions for:
- Device inventory (hardware, OS, disk, memory)
- Software inventory (installed applications)
- Patch compliance (missing updates)
- Collections membership
Map to MECM v_R_System, v_GS_* views.
```

**File: `services/mecm-connector/src/mecm_connector/queries.py`**

```python
"""MECM SQL query definitions."""


class MECMQueries:
    """SQL queries for MECM data extraction."""
    
    # Device inventory query
    DEVICES_BASE = """
    SELECT 
        sys.ResourceID AS device_id,
        sys.Name0 AS device_name,
        sys.Client0 AS is_client,
        sys.Active0 AS is_active,
        os.Caption0 AS operating_system,
        os.Version0 AS os_version,
        os.BuildNumber0 AS os_build,
        cs.Manufacturer0 AS manufacturer,
        cs.Model0 AS model,
        bios.SerialNumber0 AS serial_number,
        adapter.IPAddress0 AS ip_address,
        adapter.MACAddress0 AS mac_address,
        sys.Last_Logon_Timestamp0 AS last_logon,
        ws.LastHWScan AS last_hardware_scan,
        CAST(ISNULL(disk.FreeSpace0, 0) / 1024.0 AS DECIMAL(10,2)) AS free_disk_gb,
        CAST(ISNULL(disk.Size0, 0) / 1024.0 AS DECIMAL(10,2)) AS total_disk_gb,
        CAST(ISNULL(mem.TotalPhysicalMemory0, 0) / 1024.0 / 1024.0 AS DECIMAL(10,2)) AS memory_gb,
        proc.NumberOfCores0 AS cpu_cores,
        proc.Name0 AS cpu_name,
        usr.UniqueUserName AS primary_user,
        sys.AD_Site_Name0 AS ad_site
    FROM v_R_System sys
    LEFT JOIN v_GS_OPERATING_SYSTEM os ON sys.ResourceID = os.ResourceID
    LEFT JOIN v_GS_COMPUTER_SYSTEM cs ON sys.ResourceID = cs.ResourceID
    LEFT JOIN v_GS_PC_BIOS bios ON sys.ResourceID = bios.ResourceID
    LEFT JOIN v_GS_NETWORK_ADAPTER_CONFIGURATION adapter 
        ON sys.ResourceID = adapter.ResourceID AND adapter.IPEnabled0 = 1
    LEFT JOIN v_GS_LOGICAL_DISK disk 
        ON sys.ResourceID = disk.ResourceID AND disk.DeviceID0 = 'C:'
    LEFT JOIN v_GS_X86_PC_MEMORY mem ON sys.ResourceID = mem.ResourceID
    LEFT JOIN v_GS_PROCESSOR proc ON sys.ResourceID = proc.ResourceID
    LEFT JOIN v_GS_WORKSTATION_STATUS ws ON sys.ResourceID = ws.ResourceID
    LEFT JOIN v_R_User_Machines_List_Unique usr ON sys.ResourceID = usr.MachineID
    WHERE sys.Client0 = 1
    """
    
    DEVICES_COUNT = """
    SELECT COUNT(DISTINCT sys.ResourceID) AS total
    FROM v_R_System sys
    WHERE sys.Client0 = 1
    """
    
    # Device by ID
    DEVICE_BY_ID = DEVICES_BASE + " AND sys.ResourceID = ?"
    
    # Device search filters
    DEVICE_FILTERS = {
        "search": "AND (sys.Name0 LIKE ? OR usr.UniqueUserName LIKE ?)",
        "operating_system": "AND os.Caption0 LIKE ?",
        "manufacturer": "AND cs.Manufacturer0 LIKE ?",
        "min_disk_free": "AND (disk.FreeSpace0 / 1024.0) >= ?",
        "max_disk_free": "AND (disk.FreeSpace0 / 1024.0) <= ?",
        "inactive_days": "AND sys.Last_Logon_Timestamp0 < DATEADD(day, -?, GETDATE())",
    }
    
    # Software inventory
    SOFTWARE_BASE = """
    SELECT 
        arp.ResourceID AS device_id,
        arp.DisplayName0 AS app_name,
        arp.Version0 AS app_version,
        arp.Publisher0 AS publisher,
        arp.InstallDate0 AS install_date,
        sys.Name0 AS device_name
    FROM v_GS_ADD_REMOVE_PROGRAMS arp
    INNER JOIN v_R_System sys ON arp.ResourceID = sys.ResourceID
    WHERE arp.DisplayName0 IS NOT NULL
    """
    
    # Software for specific device
    DEVICE_SOFTWARE = SOFTWARE_BASE + " AND arp.ResourceID = ? ORDER BY arp.DisplayName0"
    
    # Application summary (aggregate by app)
    APPLICATIONS_SUMMARY = """
    SELECT 
        arp.DisplayName0 AS app_name,
        arp.Publisher0 AS publisher,
        MAX(arp.Version0) AS latest_version,
        COUNT(DISTINCT arp.ResourceID) AS install_count
    FROM v_GS_ADD_REMOVE_PROGRAMS arp
    WHERE arp.DisplayName0 IS NOT NULL
    GROUP BY arp.DisplayName0, arp.Publisher0
    """
    
    # Patch compliance - missing updates
    MISSING_PATCHES = """
    SELECT 
        ui.ResourceID AS device_id,
        sys.Name0 AS device_name,
        ui.Title AS patch_title,
        ui.BulletinID AS bulletin_id,
        ui.ArticleID AS kb_article,
        ui.DatePosted AS date_posted,
        ui.Severity AS severity,
        CASE 
            WHEN ui.Severity >= 10 THEN 'Critical'
            WHEN ui.Severity >= 6 THEN 'Important'
            WHEN ui.Severity >= 2 THEN 'Moderate'
            ELSE 'Low'
        END AS severity_name
    FROM v_UpdateComplianceStatus ucs
    INNER JOIN v_UpdateInfo ui ON ucs.CI_ID = ui.CI_ID
    INNER JOIN v_R_System sys ON ucs.ResourceID = sys.ResourceID
    WHERE ucs.Status = 2  -- Missing
    """
    
    # Missing patches for device
    DEVICE_MISSING_PATCHES = MISSING_PATCHES + " AND ucs.ResourceID = ? ORDER BY ui.Severity DESC"
    
    # Missing patch counts
    DEVICE_PATCH_COUNTS = """
    SELECT 
        sys.ResourceID AS device_id,
        COUNT(CASE WHEN ui.Severity >= 10 THEN 1 END) AS critical_count,
        COUNT(*) AS total_missing
    FROM v_UpdateComplianceStatus ucs
    INNER JOIN v_UpdateInfo ui ON ucs.CI_ID = ui.CI_ID
    INNER JOIN v_R_System sys ON ucs.ResourceID = sys.ResourceID
    WHERE ucs.Status = 2
    GROUP BY sys.ResourceID
    """
    
    # Collections
    DEVICE_COLLECTIONS = """
    SELECT 
        col.CollectionID,
        col.Name AS collection_name,
        cm.ResourceID AS device_id
    FROM v_Collection col
    INNER JOIN v_CM_RES_COLL_DEVICE cm ON col.CollectionID = cm.CollectionID
    WHERE cm.ResourceID = ?
    """
    
    ALL_COLLECTIONS = """
    SELECT 
        col.CollectionID,
        col.Name AS collection_name,
        col.MemberCount,
        col.CollectionType
    FROM v_Collection col
    WHERE col.CollectionType = 2  -- Device collections
    ORDER BY col.Name
    """
```

---

## Step 4: Device Repository

📝 **PROMPT: Create device repository with caching**
```
Create a device repository class that:
- Executes MECM queries with filtering and pagination
- Caches results in Redis with TTL
- Supports streaming for large result sets
- Maps MECM data to domain models
```

**File: `services/mecm-connector/src/mecm_connector/repositories/devices.py`**

```python
"""Device repository for MECM data access."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import redis.asyncio as redis
import structlog

from mecm_connector.config import get_settings
from mecm_connector.database import get_mecm_db
from mecm_connector.queries import MECMQueries

logger = structlog.get_logger()


class DeviceRepository:
    """Repository for device data from MECM."""
    
    def __init__(self, cache: Optional[redis.Redis] = None):
        self.settings = get_settings()
        self.cache = cache
        self.queries = MECMQueries()
    
    async def get_devices(
        self,
        search: Optional[str] = None,
        operating_system: Optional[str] = None,
        manufacturer: Optional[str] = None,
        min_disk_free: Optional[float] = None,
        max_disk_free: Optional[float] = None,
        inactive_days: Optional[int] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "device_name",
        sort_order: str = "asc",
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get devices with filtering and pagination.
        
        Returns:
            Tuple of (devices list, total count)
        """
        db = await get_mecm_db()
        
        # Build query
        query = self.queries.DEVICES_BASE
        params = []
        
        # Apply filters
        if search:
            query += " AND (sys.Name0 LIKE ? OR usr.UniqueUserName LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param])
        
        if operating_system:
            query += " AND os.Caption0 LIKE ?"
            params.append(f"%{operating_system}%")
        
        if manufacturer:
            query += " AND cs.Manufacturer0 LIKE ?"
            params.append(f"%{manufacturer}%")
        
        if min_disk_free is not None:
            query += " AND (disk.FreeSpace0 / 1024.0) >= ?"
            params.append(min_disk_free)
        
        if max_disk_free is not None:
            query += " AND (disk.FreeSpace0 / 1024.0) <= ?"
            params.append(max_disk_free)
        
        if inactive_days is not None:
            query += " AND sys.Last_Logon_Timestamp0 < DATEADD(day, -?, GETDATE())"
            params.append(inactive_days)
        
        # Get count
        count_query = f"SELECT COUNT(*) FROM ({query}) AS counted"
        total = await db.execute_scalar(count_query, tuple(params))
        
        # Apply sorting
        sort_column_map = {
            "device_name": "device_name",
            "operating_system": "operating_system",
            "free_disk_gb": "free_disk_gb",
            "last_logon": "last_logon",
        }
        sort_col = sort_column_map.get(sort_by, "device_name")
        query += f" ORDER BY {sort_col} {sort_order.upper()}"
        
        # Apply pagination
        offset = (page - 1) * page_size
        query += f" OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY"
        
        # Execute
        devices = await db.execute_query(query, tuple(params))
        
        # Transform results
        results = [self._transform_device(d) for d in devices]
        
        return results, total
    
    async def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get single device by ID."""
        # Check cache
        if self.cache:
            cached = await self.cache.get(f"device:{device_id}")
            if cached:
                return json.loads(cached)
        
        db = await get_mecm_db()
        query = self.queries.DEVICE_BY_ID
        
        results = await db.execute_query(query, (device_id,))
        
        if not results:
            return None
        
        device = self._transform_device(results[0])
        
        # Cache result
        if self.cache:
            await self.cache.setex(
                f"device:{device_id}",
                self.settings.cache_ttl_devices,
                json.dumps(device, default=str),
            )
        
        return device
    
    async def get_device_software(self, device_id: str) -> List[Dict[str, Any]]:
        """Get software installed on a device."""
        db = await get_mecm_db()
        
        results = await db.execute_query(
            self.queries.DEVICE_SOFTWARE,
            (device_id,),
        )
        
        return [
            {
                "app_name": r["app_name"],
                "version": r["app_version"],
                "publisher": r["publisher"],
                "install_date": r["install_date"],
            }
            for r in results
        ]
    
    async def get_device_patches(self, device_id: str) -> Dict[str, Any]:
        """Get patch compliance for a device."""
        db = await get_mecm_db()
        
        # Get missing patches
        missing = await db.execute_query(
            self.queries.DEVICE_MISSING_PATCHES,
            (device_id,),
        )
        
        # Group by severity
        critical = [p for p in missing if p["severity_name"] == "Critical"]
        important = [p for p in missing if p["severity_name"] == "Important"]
        moderate = [p for p in missing if p["severity_name"] == "Moderate"]
        low = [p for p in missing if p["severity_name"] == "Low"]
        
        return {
            "total_missing": len(missing),
            "critical_count": len(critical),
            "important_count": len(important),
            "moderate_count": len(moderate),
            "low_count": len(low),
            "missing_patches": [
                {
                    "title": p["patch_title"],
                    "kb_article": p["kb_article"],
                    "severity": p["severity_name"],
                    "date_posted": p["date_posted"],
                }
                for p in missing[:50]  # Limit to 50 for response size
            ],
        }
    
    async def get_device_collections(self, device_id: str) -> List[Dict[str, Any]]:
        """Get collections a device belongs to."""
        db = await get_mecm_db()
        
        results = await db.execute_query(
            self.queries.DEVICE_COLLECTIONS,
            (device_id,),
        )
        
        return [
            {
                "collection_id": r["CollectionID"],
                "collection_name": r["collection_name"],
            }
            for r in results
        ]
    
    async def query_devices(
        self,
        conditions: Dict[str, Any],
        entity_type: str = "devices",
    ) -> List[Dict[str, Any]]:
        """
        Query devices based on rule conditions.
        
        Used by the scan engine to find matching devices.
        """
        from mecm_connector.query_builder import MECMQueryBuilder
        
        db = await get_mecm_db()
        builder = MECMQueryBuilder()
        
        # Build query from conditions
        query, params = builder.build_query(conditions, entity_type)
        
        # Execute with streaming for large results
        results = []
        async for device in db.execute_query_streaming(query, tuple(params)):
            results.append(self._transform_device(device))
        
        return results
    
    def _transform_device(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw MECM data to domain model."""
        return {
            "id": str(raw.get("device_id", "")),
            "name": raw.get("device_name", ""),
            "operating_system": raw.get("operating_system", ""),
            "os_version": raw.get("os_version"),
            "os_build": raw.get("os_build"),
            "manufacturer": raw.get("manufacturer"),
            "model": raw.get("model"),
            "serial_number": raw.get("serial_number"),
            "ip_address": raw.get("ip_address"),
            "mac_address": raw.get("mac_address"),
            "last_logon": raw.get("last_logon"),
            "last_hardware_scan": raw.get("last_hardware_scan"),
            "free_disk_gb": float(raw.get("free_disk_gb") or 0),
            "total_disk_gb": float(raw.get("total_disk_gb") or 0),
            "memory_gb": float(raw.get("memory_gb") or 0),
            "cpu_cores": raw.get("cpu_cores"),
            "cpu_name": raw.get("cpu_name"),
            "primary_user": raw.get("primary_user"),
            "ad_site": raw.get("ad_site"),
            "is_active": bool(raw.get("is_active")),
        }
```

---

## Step 5: MECM Query Builder

**File: `services/mecm-connector/src/mecm_connector/query_builder.py`**

```python
"""Query builder for MECM-specific SQL queries."""

from typing import Any, Dict, List, Tuple


class MECMQueryBuilder:
    """Builds SQL queries from rule conditions for MECM."""
    
    # Field mappings from rule fields to MECM columns
    FIELD_MAPPINGS = {
        # Device fields
        "device_name": "sys.Name0",
        "operating_system": "os.Caption0",
        "os_version": "os.Version0",
        "free_disk_gb": "(disk.FreeSpace0 / 1024.0)",
        "total_disk_gb": "(disk.Size0 / 1024.0)",
        "memory_gb": "(mem.TotalPhysicalMemory0 / 1024.0 / 1024.0)",
        "cpu_cores": "proc.NumberOfCores0",
        "manufacturer": "cs.Manufacturer0",
        "model": "cs.Model0",
        "serial_number": "bios.SerialNumber0",
        "primary_user": "usr.UniqueUserName",
        "last_active_days": "DATEDIFF(day, sys.Last_Logon_Timestamp0, GETDATE())",
        "last_hardware_scan_days": "DATEDIFF(day, ws.LastHWScan, GETDATE())",
        
        # Application fields (require different base query)
        "app_name": "arp.DisplayName0",
        "app_version": "arp.Version0",
        "publisher": "arp.Publisher0",
    }
    
    # Operator mappings to SQL
    OPERATOR_MAPPINGS = {
        "eq": "= ?",
        "neq": "<> ?",
        "gt": "> ?",
        "gte": ">= ?",
        "lt": "< ?",
        "lte": "<= ?",
        "contains": "LIKE ?",
        "not_contains": "NOT LIKE ?",
        "starts_with": "LIKE ?",
        "ends_with": "LIKE ?",
        "in": "IN ({placeholders})",
        "not_in": "NOT IN ({placeholders})",
        "is_null": "IS NULL",
        "is_not_null": "IS NOT NULL",
        "older_than_days": "> ?",
        "newer_than_days": "< ?",
    }
    
    def __init__(self):
        pass
    
    def build_query(
        self,
        conditions: Dict[str, Any],
        entity_type: str = "devices",
    ) -> Tuple[str, List[Any]]:
        """
        Build SQL query from rule conditions.
        
        Args:
            conditions: Rule condition dictionary
            entity_type: Type of entity to query
            
        Returns:
            Tuple of (SQL query string, parameters list)
        """
        # Get base query
        base_query = self._get_base_query(entity_type)
        
        # Build WHERE clause
        where_clause, params = self._build_where_clause(conditions)
        
        # Combine
        query = f"{base_query} WHERE sys.Client0 = 1 AND {where_clause}"
        
        return query, params
    
    def _get_base_query(self, entity_type: str) -> str:
        """Get base query for entity type."""
        if entity_type == "devices":
            return """
            SELECT 
                sys.ResourceID AS device_id,
                sys.Name0 AS device_name,
                os.Caption0 AS operating_system,
                os.Version0 AS os_version,
                cs.Manufacturer0 AS manufacturer,
                cs.Model0 AS model,
                bios.SerialNumber0 AS serial_number,
                CAST(ISNULL(disk.FreeSpace0, 0) / 1024.0 AS DECIMAL(10,2)) AS free_disk_gb,
                CAST(ISNULL(disk.Size0, 0) / 1024.0 AS DECIMAL(10,2)) AS total_disk_gb,
                sys.Last_Logon_Timestamp0 AS last_logon,
                ws.LastHWScan AS last_hardware_scan
            FROM v_R_System sys
            LEFT JOIN v_GS_OPERATING_SYSTEM os ON sys.ResourceID = os.ResourceID
            LEFT JOIN v_GS_COMPUTER_SYSTEM cs ON sys.ResourceID = cs.ResourceID
            LEFT JOIN v_GS_PC_BIOS bios ON sys.ResourceID = bios.ResourceID
            LEFT JOIN v_GS_LOGICAL_DISK disk 
                ON sys.ResourceID = disk.ResourceID AND disk.DeviceID0 = 'C:'
            LEFT JOIN v_GS_WORKSTATION_STATUS ws ON sys.ResourceID = ws.ResourceID
            """
        elif entity_type == "applications":
            return """
            SELECT 
                arp.DisplayName0 AS app_name,
                arp.Version0 AS app_version,
                arp.Publisher0 AS publisher,
                COUNT(DISTINCT arp.ResourceID) AS install_count
            FROM v_GS_ADD_REMOVE_PROGRAMS arp
            INNER JOIN v_R_System sys ON arp.ResourceID = sys.ResourceID
            """
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
    
    def _build_where_clause(
        self,
        conditions: Dict[str, Any],
    ) -> Tuple[str, List[Any]]:
        """Build WHERE clause from conditions."""
        logic = conditions.get("logic", "AND")
        condition_list = conditions.get("conditions", [])
        
        clauses = []
        params = []
        
        for cond in condition_list:
            if "logic" in cond:
                # Nested condition group
                nested_clause, nested_params = self._build_where_clause(cond)
                clauses.append(f"({nested_clause})")
                params.extend(nested_params)
            else:
                # Single condition
                clause, cond_params = self._build_condition(cond)
                if clause:
                    clauses.append(clause)
                    params.extend(cond_params)
        
        if not clauses:
            return "1=1", []
        
        return f" {logic} ".join(clauses), params
    
    def _build_condition(
        self,
        condition: Dict[str, Any],
    ) -> Tuple[str, List[Any]]:
        """Build single condition SQL."""
        field = condition.get("field", "")
        operator = condition.get("operator", "")
        value = condition.get("value")
        
        # Get SQL column
        sql_column = self.FIELD_MAPPINGS.get(field)
        if not sql_column:
            raise ValueError(f"Unknown field: {field}")
        
        # Get SQL operator
        sql_operator = self.OPERATOR_MAPPINGS.get(operator)
        if not sql_operator:
            raise ValueError(f"Unknown operator: {operator}")
        
        # Handle special operators
        if operator == "is_null":
            return f"{sql_column} IS NULL", []
        
        if operator == "is_not_null":
            return f"{sql_column} IS NOT NULL", []
        
        if operator in ("in", "not_in"):
            if not isinstance(value, list):
                value = [value]
            placeholders = ", ".join(["?"] * len(value))
            sql = f"{sql_column} {sql_operator.replace('{placeholders}', placeholders)}"
            return sql, value
        
        if operator == "contains":
            return f"{sql_column} LIKE ?", [f"%{value}%"]
        
        if operator == "starts_with":
            return f"{sql_column} LIKE ?", [f"{value}%"]
        
        if operator == "ends_with":
            return f"{sql_column} LIKE ?", [f"%{value}"]
        
        if operator in ("older_than_days", "newer_than_days"):
            # For date comparisons, the field should be a DATEDIFF
            return f"{sql_column} {sql_operator}", [value]
        
        return f"{sql_column} {sql_operator}", [value]
```

---

## Step 6: API Routes

**File: `services/mecm-connector/src/mecm_connector/routes.py`**

```python
"""MECM Connector API routes."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from mecm_connector.repositories.devices import DeviceRepository


router = APIRouter(prefix="/api", tags=["MECM"])


class QueryConditions(BaseModel):
    """Rule conditions for device query."""
    logic: str = "AND"
    conditions: List[Dict[str, Any]]


def get_device_repo() -> DeviceRepository:
    """Get device repository instance."""
    return DeviceRepository()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    from mecm_connector.database import get_mecm_db
    
    try:
        db = await get_mecm_db()
        is_healthy = await db.health_check()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "database": "connected" if is_healthy else "disconnected",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@router.get("/devices")
async def list_devices(
    search: Optional[str] = Query(None),
    operating_system: Optional[str] = Query(None),
    manufacturer: Optional[str] = Query(None),
    min_disk_free: Optional[float] = Query(None),
    max_disk_free: Optional[float] = Query(None),
    inactive_days: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    sort_by: str = Query("device_name"),
    sort_order: str = Query("asc"),
    repo: DeviceRepository = Depends(get_device_repo),
):
    """
    List devices from MECM with filtering.
    """
    devices, total = await repo.get_devices(
        search=search,
        operating_system=operating_system,
        manufacturer=manufacturer,
        min_disk_free=min_disk_free,
        max_disk_free=max_disk_free,
        inactive_days=inactive_days,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    return {
        "items": devices,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/devices/{device_id}")
async def get_device(
    device_id: str,
    repo: DeviceRepository = Depends(get_device_repo),
):
    """
    Get device details by ID.
    """
    device = await repo.get_device(device_id)
    
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    return device


@router.get("/devices/{device_id}/software")
async def get_device_software(
    device_id: str,
    repo: DeviceRepository = Depends(get_device_repo),
):
    """
    Get software installed on a device.
    """
    return await repo.get_device_software(device_id)


@router.get("/devices/{device_id}/patches")
async def get_device_patches(
    device_id: str,
    repo: DeviceRepository = Depends(get_device_repo),
):
    """
    Get patch compliance for a device.
    """
    return await repo.get_device_patches(device_id)


@router.get("/devices/{device_id}/collections")
async def get_device_collections(
    device_id: str,
    repo: DeviceRepository = Depends(get_device_repo),
):
    """
    Get collections a device belongs to.
    """
    return await repo.get_device_collections(device_id)


@router.post("/devices/query")
async def query_devices(
    conditions: QueryConditions,
    repo: DeviceRepository = Depends(get_device_repo),
):
    """
    Query devices based on rule conditions.
    
    Used by scan engine to find matching devices.
    """
    try:
        results = await repo.query_devices(
            conditions=conditions.model_dump(),
            entity_type="devices",
        )
        return {
            "items": results,
            "total": len(results),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/collections")
async def list_collections(
    repo: DeviceRepository = Depends(get_device_repo),
):
    """
    List all MECM device collections.
    """
    from mecm_connector.database import get_mecm_db
    from mecm_connector.queries import MECMQueries
    
    db = await get_mecm_db()
    results = await db.execute_query(MECMQueries.ALL_COLLECTIONS)
    
    return [
        {
            "collection_id": r["CollectionID"],
            "name": r["collection_name"],
            "member_count": r["MemberCount"],
        }
        for r in results
    ]
```

---

## Step 7: Main Application

**File: `services/mecm-connector/src/mecm_connector/main.py`**

```python
"""MECM Connector FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from mecm_connector.config import get_settings
from mecm_connector.database import get_mecm_db, close_mecm_db
from mecm_connector.routes import router


logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info("Starting MECM Connector...")
    
    # Initialize database connection
    await get_mecm_db()
    
    yield
    
    # Cleanup
    await close_mecm_db()
    logger.info("MECM Connector shutdown complete")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="MECM Connector",
        description="Connector for Microsoft Endpoint Configuration Manager",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Internal service
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routes
    app.include_router(router)
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "mecm_connector.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
```

---

## Verification

### Test Database Connection

```powershell
# Create .env file
@"
MECM_SERVER=your-mecm-server.company.com
MECM_DATABASE=CM_ABC
MECM_USE_WINDOWS_AUTH=true
"@ | Out-File -FilePath services/mecm-connector/.env -Encoding utf8

# Start the service
cd services/mecm-connector
python -m uvicorn mecm_connector.main:app --reload --port 8002

# Test health
curl http://localhost:8002/api/health

# Test device listing
curl "http://localhost:8002/api/devices?page_size=10"
```

### Test Query Builder

```python
from mecm_connector.query_builder import MECMQueryBuilder

builder = MECMQueryBuilder()

conditions = {
    "logic": "AND",
    "conditions": [
        {"field": "operating_system", "operator": "contains", "value": "Windows 10"},
        {"field": "free_disk_gb", "operator": "lt", "value": 10}
    ]
}

query, params = builder.build_query(conditions, "devices")
print(query)
print(params)
```

---

## Common Issues

### Issue: ODBC Driver not found

**Solution:** Install SQL Server ODBC driver:

```powershell
# Windows
# Download and install from Microsoft

# Linux/Docker
apt-get update
apt-get install -y unixodbc-dev
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17
```

### Issue: Windows Authentication not working in Docker

**Solution:** Use SQL Authentication or Kerberos:

```python
# Use SQL auth in Docker
mecm_use_windows_auth = False
mecm_username = "svc_mecm_reader"
mecm_password = "secure_password"
```

### Issue: Query timeouts

**Solution:** Add pagination to queries and increase timeout:

```python
mecm_query_timeout = 300  # 5 minutes
```

---

## Next Steps

→ [07_Desktop_App.md](07_Desktop_App.md) - Implement PySide6 desktop application

---

**Checkpoint:** You should now have:
- [ ] MECM database connection working
- [ ] Device listing endpoint functional
- [ ] Device detail queries working
- [ ] Patch compliance data accessible
- [ ] Query builder translating conditions to SQL
- [ ] Caching layer implemented
