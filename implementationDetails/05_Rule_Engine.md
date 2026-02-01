# 05 - Rule Engine Implementation Guide

## Overview

This guide covers implementing the rule engine, query builder, and scan execution for the IT Operations AI Agent. The rule engine converts user-defined rules into SQL queries and executes them against the MECM database.

---

## Prerequisites

- Core service API structure created (see [04_Core_Service_API.md](04_Core_Service_API.md))
- MECM connector ready (see [06_MECM_Connector.md](06_MECM_Connector.md))
- Database models for rules and scans in place

---

## Step 1: Rule Condition Models

📝 **PROMPT: Create Pydantic models for rule conditions**
```
Create Pydantic models for a flexible rule condition system that supports:
- Multiple condition operators (equals, not_equals, contains, greater_than, less_than, in_list, etc.)
- Logical operators (AND, OR) for combining conditions
- Nested condition groups
- Field validation based on entity type (devices vs applications)
- Serialization to/from JSON for database storage
```

**File: `services/core-service/src/core_service/models/rule_conditions.py`**

```python
"""Rule condition models for flexible rule definitions."""

from enum import Enum
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class Operator(str, Enum):
    """Condition operators."""
    # Equality
    EQUALS = "eq"
    NOT_EQUALS = "neq"
    
    # Comparison
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    
    # String
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    MATCHES_REGEX = "regex"
    
    # List
    IN_LIST = "in"
    NOT_IN_LIST = "not_in"
    
    # Null
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    
    # Date/Time
    OLDER_THAN_DAYS = "older_than_days"
    NEWER_THAN_DAYS = "newer_than_days"
    BETWEEN_DATES = "between_dates"
    
    # Version comparison
    VERSION_LESS_THAN = "version_lt"
    VERSION_GREATER_THAN = "version_gt"


class LogicalOperator(str, Enum):
    """Logical operators for combining conditions."""
    AND = "AND"
    OR = "OR"


class EntityType(str, Enum):
    """Entity types for rules."""
    DEVICES = "devices"
    APPLICATIONS = "applications"
    BOTH = "both"


# Field definitions by entity type
DEVICE_FIELDS = {
    "device_name": {"type": "string", "description": "Device hostname"},
    "operating_system": {"type": "string", "description": "OS name and version"},
    "os_version": {"type": "string", "description": "OS version number"},
    "manufacturer": {"type": "string", "description": "Hardware manufacturer"},
    "model": {"type": "string", "description": "Hardware model"},
    "serial_number": {"type": "string", "description": "Serial number"},
    "last_active_date": {"type": "date", "description": "Last seen date"},
    "last_active_days": {"type": "number", "description": "Days since last active"},
    "primary_user": {"type": "string", "description": "Primary user email"},
    "site_code": {"type": "string", "description": "MECM site code"},
    "free_disk_gb": {"type": "number", "description": "Free disk space in GB"},
    "total_disk_gb": {"type": "number", "description": "Total disk space in GB"},
    "disk_usage_pct": {"type": "number", "description": "Disk usage percentage"},
    "total_memory_gb": {"type": "number", "description": "Total RAM in GB"},
    "missing_patches_count": {"type": "number", "description": "Number of missing patches"},
    "missing_critical_patches": {"type": "number", "description": "Critical patches missing"},
    "last_patch_date": {"type": "date", "description": "Last patch installation date"},
    "eol_date": {"type": "date", "description": "End of life date"},
    "eol_days_remaining": {"type": "number", "description": "Days until EOL"},
    "is_virtual": {"type": "boolean", "description": "Is virtual machine"},
    "ad_site": {"type": "string", "description": "Active Directory site"},
    "ip_address": {"type": "string", "description": "IP address"},
}

APPLICATION_FIELDS = {
    "app_name": {"type": "string", "description": "Application name"},
    "app_version": {"type": "string", "description": "Application version"},
    "publisher": {"type": "string", "description": "Software publisher"},
    "install_count": {"type": "number", "description": "Number of installations"},
    "app_owner_email": {"type": "string", "description": "Application owner email"},
    "app_owner_department": {"type": "string", "description": "Owner department"},
    "cve_count": {"type": "number", "description": "Number of CVEs"},
    "cve_list": {"type": "list", "description": "List of CVE IDs"},
    "highest_cvss": {"type": "number", "description": "Highest CVSS score"},
    "is_eol": {"type": "boolean", "description": "Is end of life"},
    "eol_date": {"type": "date", "description": "End of life date"},
    "category": {"type": "string", "description": "Application category"},
    "criticality": {"type": "string", "description": "Business criticality"},
    "license_count": {"type": "number", "description": "Licensed quantity"},
    "is_over_licensed": {"type": "boolean", "description": "Over license limit"},
}


class Condition(BaseModel):
    """Single rule condition."""
    
    field: str = Field(..., description="Field to evaluate")
    operator: Operator = Field(..., description="Comparison operator")
    value: Any = Field(default=None, description="Value to compare against")
    
    @field_validator("value", mode="before")
    @classmethod
    def validate_value(cls, v, info):
        """Validate value based on operator."""
        operator = info.data.get("operator")
        
        # Null operators don't need a value
        if operator in [Operator.IS_NULL, Operator.IS_NOT_NULL]:
            return None
        
        # List operators need a list
        if operator in [Operator.IN_LIST, Operator.NOT_IN_LIST]:
            if not isinstance(v, list):
                raise ValueError(f"Operator {operator} requires a list value")
        
        return v
    
    def to_sql_condition(self, table_alias: str = "") -> tuple[str, list]:
        """
        Convert condition to SQL WHERE clause.
        
        Returns:
            Tuple of (SQL string, list of parameters)
        """
        prefix = f"{table_alias}." if table_alias else ""
        field = f"{prefix}{self.field}"
        
        operator_map = {
            Operator.EQUALS: ("= %s", [self.value]),
            Operator.NOT_EQUALS: ("!= %s", [self.value]),
            Operator.GREATER_THAN: ("> %s", [self.value]),
            Operator.GREATER_THAN_OR_EQUAL: (">= %s", [self.value]),
            Operator.LESS_THAN: ("< %s", [self.value]),
            Operator.LESS_THAN_OR_EQUAL: ("<= %s", [self.value]),
            Operator.CONTAINS: ("LIKE %s", [f"%{self.value}%"]),
            Operator.NOT_CONTAINS: ("NOT LIKE %s", [f"%{self.value}%"]),
            Operator.STARTS_WITH: ("LIKE %s", [f"{self.value}%"]),
            Operator.ENDS_WITH: ("LIKE %s", [f"%{self.value}"]),
            Operator.IS_NULL: ("IS NULL", []),
            Operator.IS_NOT_NULL: ("IS NOT NULL", []),
            Operator.IN_LIST: (f"IN ({','.join(['%s'] * len(self.value))})", self.value),
            Operator.NOT_IN_LIST: (f"NOT IN ({','.join(['%s'] * len(self.value))})", self.value),
            Operator.OLDER_THAN_DAYS: ("< DATEADD(day, -%s, GETDATE())", [self.value]),
            Operator.NEWER_THAN_DAYS: ("> DATEADD(day, -%s, GETDATE())", [self.value]),
        }
        
        sql_op, params = operator_map.get(self.operator, ("= %s", [self.value]))
        return f"{field} {sql_op}", params


class ConditionGroup(BaseModel):
    """Group of conditions combined with logical operator."""
    
    logic: LogicalOperator = Field(default=LogicalOperator.AND)
    conditions: List[Union[Condition, "ConditionGroup"]] = Field(default_factory=list)
    
    def to_sql_condition(self, table_alias: str = "") -> tuple[str, list]:
        """
        Convert condition group to SQL WHERE clause.
        
        Returns:
            Tuple of (SQL string, list of parameters)
        """
        if not self.conditions:
            return "1=1", []
        
        sql_parts = []
        all_params = []
        
        for condition in self.conditions:
            sql, params = condition.to_sql_condition(table_alias)
            sql_parts.append(f"({sql})")
            all_params.extend(params)
        
        joiner = f" {self.logic.value} "
        return joiner.join(sql_parts), all_params
    
    def add_condition(
        self, 
        field: str, 
        operator: Operator, 
        value: Any = None
    ) -> "ConditionGroup":
        """Add a condition to the group."""
        self.conditions.append(Condition(field=field, operator=operator, value=value))
        return self


# Enable forward reference
ConditionGroup.model_rebuild()


class RuleDefinition(BaseModel):
    """Complete rule definition with conditions and metadata."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    entity_type: EntityType = Field(default=EntityType.DEVICES)
    conditions: ConditionGroup = Field(default_factory=lambda: ConditionGroup())
    
    # Target systems to query
    query_mecm: bool = Field(default=True)
    query_tachyon: bool = Field(default=False)
    
    # Severity for results
    default_severity: str = Field(default="medium")
    
    @model_validator(mode="after")
    def validate_fields_for_entity_type(self):
        """Validate that fields are appropriate for entity type."""
        valid_fields = set()
        
        if self.entity_type in [EntityType.DEVICES, EntityType.BOTH]:
            valid_fields.update(DEVICE_FIELDS.keys())
        
        if self.entity_type in [EntityType.APPLICATIONS, EntityType.BOTH]:
            valid_fields.update(APPLICATION_FIELDS.keys())
        
        # Recursively check all conditions
        def check_conditions(cond_group: ConditionGroup):
            for cond in cond_group.conditions:
                if isinstance(cond, Condition):
                    if cond.field not in valid_fields:
                        raise ValueError(
                            f"Field '{cond.field}' is not valid for entity type '{self.entity_type}'"
                        )
                elif isinstance(cond, ConditionGroup):
                    check_conditions(cond)
        
        check_conditions(self.conditions)
        return self
    
    def get_available_fields(self) -> dict:
        """Get available fields for this rule's entity type."""
        fields = {}
        
        if self.entity_type in [EntityType.DEVICES, EntityType.BOTH]:
            fields.update(DEVICE_FIELDS)
        
        if self.entity_type in [EntityType.APPLICATIONS, EntityType.BOTH]:
            fields.update(APPLICATION_FIELDS)
        
        return fields
```

---

## Step 2: Query Builder

📝 **PROMPT: Create SQL query builder for MECM**
```
Create a QueryBuilder class that:
- Converts RuleDefinition conditions into MECM SQL queries
- Handles different entity types (devices, applications)
- Joins multiple MECM tables based on required fields
- Supports pagination and result limiting
- Produces parameterized queries to prevent SQL injection
- Includes field mapping from logical names to MECM column names
```

**File: `services/core-service/src/core_service/services/query_builder.py`**

```python
"""Query builder for converting rules to MECM SQL queries."""

from typing import Any, List, Optional, Tuple

from core_service.models.rule_conditions import (
    Condition,
    ConditionGroup,
    EntityType,
    LogicalOperator,
    Operator,
    RuleDefinition,
)


# MECM field mappings
DEVICE_FIELD_MAPPING = {
    # Logical field -> (MECM table alias, MECM column name)
    "device_name": ("sys", "Name0"),
    "operating_system": ("os", "Caption0"),
    "os_version": ("os", "Version0"),
    "manufacturer": ("cs", "Manufacturer0"),
    "model": ("cs", "Model0"),
    "serial_number": ("bios", "SerialNumber0"),
    "last_active_date": ("ch", "LastActiveTime"),
    "primary_user": ("sys", "User_Name0"),
    "site_code": ("sys", "SMS_Assigned_Sites0"),
    "free_disk_gb": ("disk", "FreeSpace0"),  # Needs conversion from MB
    "total_disk_gb": ("disk", "Size0"),  # Needs conversion from MB
    "total_memory_gb": ("mem", "TotalPhysicalMemory0"),  # Needs conversion
    "ad_site": ("sys", "AD_Site_Name0"),
    "ip_address": ("net", "IPAddress0"),
    "is_virtual": ("cs", "Model0"),  # Check if contains 'Virtual'
}

APPLICATION_FIELD_MAPPING = {
    "app_name": ("sw", "DisplayName0"),
    "app_version": ("sw", "Version0"),
    "publisher": ("sw", "Publisher0"),
}


class QueryBuilder:
    """Build SQL queries for MECM database from rule definitions."""
    
    # Base tables
    DEVICE_BASE_TABLE = "v_R_System"
    APPLICATION_BASE_TABLE = "v_GS_INSTALLED_SOFTWARE"
    
    # Table join definitions
    DEVICE_JOINS = {
        "os": {
            "table": "v_GS_OPERATING_SYSTEM",
            "alias": "os",
            "on": "sys.ResourceID = os.ResourceID",
        },
        "cs": {
            "table": "v_GS_COMPUTER_SYSTEM",
            "alias": "cs",
            "on": "sys.ResourceID = cs.ResourceID",
        },
        "bios": {
            "table": "v_GS_PC_BIOS",
            "alias": "bios",
            "on": "sys.ResourceID = bios.ResourceID",
        },
        "disk": {
            "table": "v_GS_LOGICAL_DISK",
            "alias": "disk",
            "on": "sys.ResourceID = disk.ResourceID AND disk.DriveType0 = 3",
        },
        "mem": {
            "table": "v_GS_X86_PC_MEMORY",
            "alias": "mem",
            "on": "sys.ResourceID = mem.ResourceID",
        },
        "ch": {
            "table": "v_CH_ClientSummary",
            "alias": "ch",
            "on": "sys.ResourceID = ch.ResourceID",
        },
        "net": {
            "table": "v_GS_NETWORK_ADAPTER_CONFIGURATION",
            "alias": "net",
            "on": "sys.ResourceID = net.ResourceID AND net.IPEnabled0 = 1",
        },
    }
    
    def __init__(self, rule: RuleDefinition):
        self.rule = rule
        self.required_joins: set = set()
        self.parameters: list = []
    
    def build_device_query(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Tuple[str, List[Any]]:
        """
        Build SQL query for device scanning.
        
        Returns:
            Tuple of (SQL query string, parameters list)
        """
        self.parameters = []
        self.required_joins = set()
        
        # Analyze conditions to determine required joins
        self._analyze_conditions(self.rule.conditions, DEVICE_FIELD_MAPPING)
        
        # Build SELECT clause
        select_fields = self._build_device_select()
        
        # Build FROM clause with joins
        from_clause = self._build_device_from()
        
        # Build WHERE clause
        where_clause, where_params = self._build_where_clause(
            self.rule.conditions, 
            DEVICE_FIELD_MAPPING
        )
        self.parameters.extend(where_params)
        
        # Build complete query
        query = f"""
        SELECT {select_fields}
        FROM {from_clause}
        WHERE sys.Decommissioned0 = 0
          AND sys.Obsolete0 = 0
          AND ({where_clause})
        ORDER BY sys.Name0
        """
        
        # Add pagination
        if limit:
            query += f"\nOFFSET {offset or 0} ROWS FETCH NEXT {limit} ROWS ONLY"
        
        return query.strip(), self.parameters
    
    def build_application_query(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Tuple[str, List[Any]]:
        """
        Build SQL query for application scanning.
        
        Returns:
            Tuple of (SQL query string, parameters list)
        """
        self.parameters = []
        
        # Build WHERE clause
        where_clause, where_params = self._build_where_clause(
            self.rule.conditions,
            APPLICATION_FIELD_MAPPING
        )
        self.parameters.extend(where_params)
        
        query = f"""
        SELECT 
            sw.DisplayName0 AS app_name,
            sw.Version0 AS app_version,
            sw.Publisher0 AS publisher,
            COUNT(DISTINCT sw.ResourceID) AS install_count,
            STRING_AGG(CAST(sw.ResourceID AS VARCHAR), ',') AS device_ids
        FROM v_GS_INSTALLED_SOFTWARE sw
        WHERE ({where_clause})
        GROUP BY sw.DisplayName0, sw.Version0, sw.Publisher0
        ORDER BY install_count DESC
        """
        
        if limit:
            query += f"\nOFFSET {offset or 0} ROWS FETCH NEXT {limit} ROWS ONLY"
        
        return query.strip(), self.parameters
    
    def _analyze_conditions(
        self, 
        condition_group: ConditionGroup,
        field_mapping: dict
    ):
        """Analyze conditions to determine required table joins."""
        for condition in condition_group.conditions:
            if isinstance(condition, Condition):
                if condition.field in field_mapping:
                    table_alias, _ = field_mapping[condition.field]
                    if table_alias != "sys":
                        self.required_joins.add(table_alias)
            elif isinstance(condition, ConditionGroup):
                self._analyze_conditions(condition, field_mapping)
    
    def _build_device_select(self) -> str:
        """Build SELECT clause for device query."""
        fields = [
            "sys.ResourceID AS resource_id",
            "sys.Name0 AS device_name",
            "sys.User_Name0 AS primary_user",
            "sys.AD_Site_Name0 AS ad_site",
        ]
        
        # Add fields based on required joins
        if "os" in self.required_joins or True:  # Always include OS
            fields.extend([
                "os.Caption0 AS operating_system",
                "os.Version0 AS os_version",
            ])
        
        if "cs" in self.required_joins or True:
            fields.extend([
                "cs.Manufacturer0 AS manufacturer",
                "cs.Model0 AS model",
            ])
        
        if "disk" in self.required_joins:
            fields.extend([
                "disk.FreeSpace0 / 1024.0 AS free_disk_gb",
                "disk.Size0 / 1024.0 AS total_disk_gb",
            ])
        
        if "ch" in self.required_joins:
            fields.append("ch.LastActiveTime AS last_active_date")
        
        return ",\n            ".join(fields)
    
    def _build_device_from(self) -> str:
        """Build FROM clause with required joins."""
        from_parts = [f"{self.DEVICE_BASE_TABLE} sys"]
        
        # Always join OS and CS for basic info
        self.required_joins.update(["os", "cs"])
        
        for alias in self.required_joins:
            if alias in self.DEVICE_JOINS:
                join_def = self.DEVICE_JOINS[alias]
                from_parts.append(
                    f"LEFT JOIN {join_def['table']} {join_def['alias']} "
                    f"ON {join_def['on']}"
                )
        
        return "\n        ".join(from_parts)
    
    def _build_where_clause(
        self,
        condition_group: ConditionGroup,
        field_mapping: dict
    ) -> Tuple[str, List[Any]]:
        """Build WHERE clause from conditions."""
        if not condition_group.conditions:
            return "1=1", []
        
        sql_parts = []
        params = []
        
        for condition in condition_group.conditions:
            if isinstance(condition, Condition):
                sql, condition_params = self._condition_to_sql(
                    condition, 
                    field_mapping
                )
                sql_parts.append(f"({sql})")
                params.extend(condition_params)
            elif isinstance(condition, ConditionGroup):
                sql, group_params = self._build_where_clause(
                    condition, 
                    field_mapping
                )
                sql_parts.append(f"({sql})")
                params.extend(group_params)
        
        joiner = f" {condition_group.logic.value} "
        return joiner.join(sql_parts), params
    
    def _condition_to_sql(
        self,
        condition: Condition,
        field_mapping: dict
    ) -> Tuple[str, List[Any]]:
        """Convert single condition to SQL."""
        if condition.field not in field_mapping:
            raise ValueError(f"Unknown field: {condition.field}")
        
        table_alias, column_name = field_mapping[condition.field]
        field_ref = f"{table_alias}.{column_name}"
        
        # Handle special field transformations
        if condition.field == "free_disk_gb":
            field_ref = f"({table_alias}.{column_name} / 1024.0)"
        elif condition.field == "total_disk_gb":
            field_ref = f"({table_alias}.{column_name} / 1024.0)"
        elif condition.field == "last_active_days":
            field_ref = f"DATEDIFF(day, {table_alias}.LastActiveTime, GETDATE())"
        
        # Convert operator to SQL
        return self._operator_to_sql(field_ref, condition.operator, condition.value)
    
    def _operator_to_sql(
        self,
        field_ref: str,
        operator: Operator,
        value: Any
    ) -> Tuple[str, List[Any]]:
        """Convert operator to SQL syntax."""
        if operator == Operator.EQUALS:
            return f"{field_ref} = ?", [value]
        elif operator == Operator.NOT_EQUALS:
            return f"{field_ref} != ?", [value]
        elif operator == Operator.GREATER_THAN:
            return f"{field_ref} > ?", [value]
        elif operator == Operator.GREATER_THAN_OR_EQUAL:
            return f"{field_ref} >= ?", [value]
        elif operator == Operator.LESS_THAN:
            return f"{field_ref} < ?", [value]
        elif operator == Operator.LESS_THAN_OR_EQUAL:
            return f"{field_ref} <= ?", [value]
        elif operator == Operator.CONTAINS:
            return f"{field_ref} LIKE ?", [f"%{value}%"]
        elif operator == Operator.NOT_CONTAINS:
            return f"{field_ref} NOT LIKE ?", [f"%{value}%"]
        elif operator == Operator.STARTS_WITH:
            return f"{field_ref} LIKE ?", [f"{value}%"]
        elif operator == Operator.ENDS_WITH:
            return f"{field_ref} LIKE ?", [f"%{value}"]
        elif operator == Operator.IS_NULL:
            return f"{field_ref} IS NULL", []
        elif operator == Operator.IS_NOT_NULL:
            return f"{field_ref} IS NOT NULL", []
        elif operator == Operator.IN_LIST:
            placeholders = ",".join(["?"] * len(value))
            return f"{field_ref} IN ({placeholders})", list(value)
        elif operator == Operator.NOT_IN_LIST:
            placeholders = ",".join(["?"] * len(value))
            return f"{field_ref} NOT IN ({placeholders})", list(value)
        elif operator == Operator.OLDER_THAN_DAYS:
            return f"{field_ref} < DATEADD(day, -?, GETDATE())", [value]
        elif operator == Operator.NEWER_THAN_DAYS:
            return f"{field_ref} > DATEADD(day, -?, GETDATE())", [value]
        else:
            raise ValueError(f"Unsupported operator: {operator}")


def build_query_from_rule(
    rule: RuleDefinition,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> Tuple[str, List[Any]]:
    """
    Convenience function to build query from rule.
    
    Returns:
        Tuple of (SQL query, parameters)
    """
    builder = QueryBuilder(rule)
    
    if rule.entity_type == EntityType.DEVICES:
        return builder.build_device_query(limit, offset)
    elif rule.entity_type == EntityType.APPLICATIONS:
        return builder.build_application_query(limit, offset)
    else:
        # For BOTH, return device query (applications handled separately)
        return builder.build_device_query(limit, offset)
```

---

## Step 3: Scan Engine

📝 **PROMPT: Create async scan execution engine**
```
Create an async scan engine class that:
- Executes rules against MECM database
- Handles large result sets with streaming/chunking
- Tracks scan progress and updates status
- Calculates severity for each result
- Stores results in PostgreSQL
- Supports cancellation
- Logs execution metrics
```

**File: `services/core-service/src/core_service/services/scan_engine.py`**

```python
"""Scan execution engine for running rules against data sources."""

import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import uuid4

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.connectors.mecm import MECMConnector
from core_service.models.rule import Rule, EntityType
from core_service.models.scan import Scan, ScanResult, ScanStatus, Severity
from core_service.models.rule_conditions import RuleDefinition
from core_service.services.query_builder import QueryBuilder

logger = structlog.get_logger()


class ScanEngine:
    """Execute scans against data sources."""
    
    CHUNK_SIZE = 1000  # Process results in chunks
    
    def __init__(
        self,
        db_session: AsyncSession,
        mecm_connector: MECMConnector,
    ):
        self.db = db_session
        self.mecm = mecm_connector
        self._cancelled: Dict[str, bool] = {}
    
    async def execute_scan(
        self,
        rule: Rule,
        user_id: str,
    ) -> Scan:
        """
        Execute a rule scan.
        
        Args:
            rule: Rule to execute
            user_id: ID of user initiating scan
            
        Returns:
            Scan record with results
        """
        # Create scan record
        scan = Scan(
            id=str(uuid4()),
            rule_id=rule.id,
            rule_name=rule.name,
            status=ScanStatus.PENDING,
            created_by_id=user_id,
        )
        self.db.add(scan)
        await self.db.commit()
        
        self._cancelled[scan.id] = False
        
        try:
            # Update status to running
            scan.status = ScanStatus.RUNNING
            scan.started_at = datetime.now(timezone.utc)
            await self.db.commit()
            
            logger.info(
                "Starting scan",
                scan_id=scan.id,
                rule_name=rule.name,
                entity_type=rule.entity_type.value,
            )
            
            # Build rule definition from stored conditions
            rule_def = RuleDefinition(
                name=rule.name,
                description=rule.description,
                entity_type=rule.entity_type,
                conditions=rule.conditions,
            )
            
            # Execute based on entity type
            total_matched = 0
            devices_matched = 0
            apps_matched = 0
            
            if rule.entity_type in [EntityType.DEVICES, EntityType.BOTH]:
                devices_matched = await self._scan_devices(
                    scan, rule_def
                )
                total_matched += devices_matched
            
            if rule.entity_type in [EntityType.APPLICATIONS, EntityType.BOTH]:
                apps_matched = await self._scan_applications(
                    scan, rule_def
                )
                total_matched += apps_matched
            
            # Check if cancelled
            if self._cancelled.get(scan.id):
                scan.status = ScanStatus.CANCELLED
            else:
                scan.status = ScanStatus.COMPLETED
            
            scan.completed_at = datetime.now(timezone.utc)
            scan.total_matched = total_matched
            scan.devices_matched = devices_matched
            scan.applications_matched = apps_matched
            
            await self.db.commit()
            
            logger.info(
                "Scan completed",
                scan_id=scan.id,
                total_matched=total_matched,
                duration_seconds=scan.duration_seconds,
            )
            
            return scan
            
        except Exception as e:
            logger.error(
                "Scan failed",
                scan_id=scan.id,
                error=str(e),
            )
            
            scan.status = ScanStatus.FAILED
            scan.error_message = str(e)
            scan.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            
            raise
        
        finally:
            # Cleanup
            self._cancelled.pop(scan.id, None)
    
    async def cancel_scan(self, scan_id: str) -> bool:
        """Cancel a running scan."""
        self._cancelled[scan_id] = True
        
        # Update database status
        await self.db.execute(
            update(Scan)
            .where(Scan.id == scan_id)
            .where(Scan.status == ScanStatus.RUNNING)
            .values(status=ScanStatus.CANCELLED)
        )
        await self.db.commit()
        
        return True
    
    async def _scan_devices(
        self,
        scan: Scan,
        rule_def: RuleDefinition,
    ) -> int:
        """Scan devices and store results."""
        builder = QueryBuilder(rule_def)
        query, params = builder.build_device_query()
        
        total_count = 0
        
        # Stream results in chunks
        async for chunk in self._stream_mecm_results(query, params):
            if self._cancelled.get(scan.id):
                break
            
            # Process chunk
            results = []
            for row in chunk:
                severity = self._calculate_severity(row, rule_def)
                
                result = ScanResult(
                    scan_id=scan.id,
                    entity_type="device",
                    entity_id=str(row.get("resource_id")),
                    entity_name=row.get("device_name", "Unknown"),
                    match_data=dict(row),
                    severity=severity,
                )
                results.append(result)
            
            # Bulk insert
            self.db.add_all(results)
            await self.db.commit()
            
            total_count += len(results)
            
            # Update scan progress
            scan.total_scanned += len(chunk)
            await self.db.commit()
        
        return total_count
    
    async def _scan_applications(
        self,
        scan: Scan,
        rule_def: RuleDefinition,
    ) -> int:
        """Scan applications and store results."""
        builder = QueryBuilder(rule_def)
        query, params = builder.build_application_query()
        
        total_count = 0
        
        async for chunk in self._stream_mecm_results(query, params):
            if self._cancelled.get(scan.id):
                break
            
            results = []
            for row in chunk:
                severity = self._calculate_severity(row, rule_def)
                
                result = ScanResult(
                    scan_id=scan.id,
                    entity_type="application",
                    entity_id=f"{row.get('app_name')}|{row.get('app_version')}",
                    entity_name=row.get("app_name", "Unknown"),
                    match_data=dict(row),
                    severity=severity,
                )
                results.append(result)
            
            self.db.add_all(results)
            await self.db.commit()
            
            total_count += len(results)
        
        return total_count
    
    async def _stream_mecm_results(
        self,
        query: str,
        params: List[Any],
    ) -> AsyncGenerator[List[Dict], None]:
        """Stream query results in chunks."""
        offset = 0
        
        while True:
            chunk_query = f"{query}\nOFFSET {offset} ROWS FETCH NEXT {self.CHUNK_SIZE} ROWS ONLY"
            
            results = await self.mecm.execute_query(chunk_query, params)
            
            if not results:
                break
            
            yield results
            
            if len(results) < self.CHUNK_SIZE:
                break
            
            offset += self.CHUNK_SIZE
            
            # Small delay to prevent overwhelming the database
            await asyncio.sleep(0.1)
    
    def _calculate_severity(
        self,
        row: Dict[str, Any],
        rule_def: RuleDefinition,
    ) -> Severity:
        """Calculate severity based on result data."""
        # Default severity from rule
        default = Severity(rule_def.default_severity)
        
        # Upgrade severity based on specific conditions
        free_disk = row.get("free_disk_gb")
        if free_disk is not None:
            if free_disk < 5:
                return Severity.CRITICAL
            elif free_disk < 10:
                return Severity.HIGH
        
        cve_count = row.get("cve_count")
        if cve_count is not None:
            if cve_count > 5:
                return Severity.CRITICAL
            elif cve_count > 0:
                return Severity.HIGH
        
        missing_patches = row.get("missing_critical_patches")
        if missing_patches is not None and missing_patches > 10:
            return Severity.HIGH
        
        return default


class ScanScheduler:
    """Schedule and manage recurring scans."""
    
    def __init__(
        self,
        db_session: AsyncSession,
        scan_engine: ScanEngine,
    ):
        self.db = db_session
        self.engine = scan_engine
        self._tasks: Dict[str, asyncio.Task] = {}
    
    async def schedule_rule(self, rule: Rule) -> None:
        """Schedule a rule for periodic execution."""
        if not rule.schedule_enabled or not rule.schedule_cron:
            return
        
        # Parse cron expression and create task
        # This is a simplified implementation
        # For production, use APScheduler or similar
        
        logger.info(
            "Rule scheduled",
            rule_id=rule.id,
            cron=rule.schedule_cron,
        )
    
    async def unschedule_rule(self, rule_id: str) -> None:
        """Remove a rule from schedule."""
        if rule_id in self._tasks:
            self._tasks[rule_id].cancel()
            del self._tasks[rule_id]
```

---

## Step 4: Natural Language Rule Parser

📝 **PROMPT: Create NL to rule condition parser**
```
Create a class that parses natural language rule descriptions and converts them to structured conditions. This will be enhanced with LLM later, but start with regex-based parsing for common patterns like:
- "devices with less than 10GB free disk space"
- "applications owned by john@example.com"
- "devices not patched in the last 30 days"
```

**File: `services/core-service/src/core_service/services/nl_parser.py`**

```python
"""Natural language parser for rule conditions."""

import re
from typing import List, Optional, Tuple

from core_service.models.rule_conditions import (
    Condition,
    ConditionGroup,
    EntityType,
    LogicalOperator,
    Operator,
)


class NLRuleParser:
    """Parse natural language into rule conditions."""
    
    # Common patterns for device rules
    DEVICE_PATTERNS = [
        # Disk space patterns
        (
            r"(?:devices?\s+)?(?:with\s+)?(?:less\s+than|under|<)\s+(\d+)\s*(?:GB|gigabytes?)?\s+(?:free\s+)?(?:disk\s+)?space",
            lambda m: Condition(field="free_disk_gb", operator=Operator.LESS_THAN, value=int(m.group(1)))
        ),
        (
            r"(?:devices?\s+)?(?:with\s+)?(?:more\s+than|over|>)\s+(\d+)\s*(?:GB|gigabytes?)?\s+(?:free\s+)?(?:disk\s+)?space",
            lambda m: Condition(field="free_disk_gb", operator=Operator.GREATER_THAN, value=int(m.group(1)))
        ),
        
        # Patch/update patterns
        (
            r"(?:devices?\s+)?(?:not\s+)?(?:patched|updated)\s+(?:in\s+)?(?:the\s+)?(?:last\s+)?(\d+)\s+days?",
            lambda m: Condition(field="last_active_days", operator=Operator.GREATER_THAN, value=int(m.group(1)))
        ),
        (
            r"(?:devices?\s+)?(?:with\s+)?(?:missing|without)\s+(?:critical\s+)?patches",
            lambda m: Condition(field="missing_critical_patches", operator=Operator.GREATER_THAN, value=0)
        ),
        
        # OS patterns
        (
            r"(?:running|with)\s+(Windows\s+\d+|Windows\s+Server\s+\d+|macOS|Linux)",
            lambda m: Condition(field="operating_system", operator=Operator.CONTAINS, value=m.group(1))
        ),
        
        # Activity patterns
        (
            r"(?:inactive|not\s+(?:seen|active))\s+(?:for\s+)?(?:more\s+than\s+)?(\d+)\s+days?",
            lambda m: Condition(field="last_active_days", operator=Operator.GREATER_THAN, value=int(m.group(1)))
        ),
        
        # Manufacturer/model
        (
            r"(?:made\s+by|manufacturer)\s+[\"']?(\w+)[\"']?",
            lambda m: Condition(field="manufacturer", operator=Operator.EQUALS, value=m.group(1))
        ),
    ]
    
    # Common patterns for application rules
    APPLICATION_PATTERNS = [
        # Version patterns
        (
            r"(?:version|v)?\s*(?:older\s+than|before|<)\s*[\"']?([^\s\"']+)[\"']?",
            lambda m: Condition(field="app_version", operator=Operator.VERSION_LESS_THAN, value=m.group(1))
        ),
        
        # Publisher patterns
        (
            r"(?:from|by|publisher)\s+[\"']?([^\s\"']+)[\"']?",
            lambda m: Condition(field="publisher", operator=Operator.CONTAINS, value=m.group(1))
        ),
        
        # CVE/vulnerability patterns
        (
            r"(?:with\s+)?(?:known\s+)?vulnerabilit(?:y|ies)|CVE",
            lambda m: Condition(field="cve_count", operator=Operator.GREATER_THAN, value=0)
        ),
        
        # App name patterns
        (
            r"(?:app(?:lication)?s?\s+)?(?:named?\s+)?[\"']([^\"']+)[\"']",
            lambda m: Condition(field="app_name", operator=Operator.CONTAINS, value=m.group(1))
        ),
    ]
    
    def __init__(self):
        self.last_confidence: float = 0.0
    
    def parse(self, text: str) -> Tuple[ConditionGroup, EntityType, float]:
        """
        Parse natural language text into conditions.
        
        Args:
            text: Natural language description
            
        Returns:
            Tuple of (ConditionGroup, EntityType, confidence score)
        """
        text = text.lower().strip()
        
        # Determine entity type
        entity_type = self._detect_entity_type(text)
        
        # Extract conditions
        conditions = []
        
        # Choose patterns based on entity type
        patterns = []
        if entity_type in [EntityType.DEVICES, EntityType.BOTH]:
            patterns.extend(self.DEVICE_PATTERNS)
        if entity_type in [EntityType.APPLICATIONS, EntityType.BOTH]:
            patterns.extend(self.APPLICATION_PATTERNS)
        
        # Match patterns
        matched_spans = []
        for pattern, builder in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                condition = builder(match)
                conditions.append(condition)
                matched_spans.append((match.start(), match.end()))
        
        # Calculate confidence based on text coverage
        if conditions:
            total_matched = sum(end - start for start, end in matched_spans)
            text_length = len(text)
            self.last_confidence = min(0.95, total_matched / text_length + 0.3)
        else:
            self.last_confidence = 0.0
        
        # Detect logical operator
        logic = self._detect_logic_operator(text)
        
        # Build condition group
        group = ConditionGroup(logic=logic, conditions=conditions)
        
        return group, entity_type, self.last_confidence
    
    def _detect_entity_type(self, text: str) -> EntityType:
        """Detect entity type from text."""
        text_lower = text.lower()
        
        has_device_keywords = any(
            kw in text_lower 
            for kw in ["device", "computer", "machine", "workstation", "server", "laptop"]
        )
        
        has_app_keywords = any(
            kw in text_lower 
            for kw in ["application", "software", "program", "app ", "apps "]
        )
        
        if has_device_keywords and has_app_keywords:
            return EntityType.BOTH
        elif has_app_keywords:
            return EntityType.APPLICATIONS
        else:
            return EntityType.DEVICES  # Default to devices
    
    def _detect_logic_operator(self, text: str) -> LogicalOperator:
        """Detect whether conditions should be AND or OR."""
        text_lower = text.lower()
        
        # Look for OR indicators
        or_indicators = [" or ", " either ", " any of "]
        if any(indicator in text_lower for indicator in or_indicators):
            return LogicalOperator.OR
        
        return LogicalOperator.AND


# Convenience function
def parse_natural_language(text: str) -> Tuple[ConditionGroup, EntityType, float]:
    """
    Parse natural language into rule conditions.
    
    Args:
        text: Natural language description
        
    Returns:
        Tuple of (ConditionGroup, EntityType, confidence score)
    """
    parser = NLRuleParser()
    return parser.parse(text)
```

---

## Step 5: Rule Service API

**File: `services/core-service/src/core_service/api/rules.py`**

```python
"""Rule management API endpoints."""

from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.models.rule import Rule, RuleTemplate, EntityType
from core_service.models.rule_conditions import (
    ConditionGroup,
    Operator,
    RuleDefinition,
)
from core_service.services.nl_parser import parse_natural_language
from core_service.services.query_builder import QueryBuilder

router = APIRouter(prefix="/api/rules", tags=["Rules"])


# Request/Response Models
class ConditionRequest(BaseModel):
    """Single condition in a rule."""
    field: str
    operator: str
    value: Optional[any] = None


class ConditionGroupRequest(BaseModel):
    """Group of conditions."""
    logic: str = "AND"
    conditions: List[ConditionRequest] = []


class ActionConfigRequest(BaseModel):
    """Action configuration."""
    type: str
    params: dict = {}


class CreateRuleRequest(BaseModel):
    """Request to create a new rule."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    entity_type: EntityType = EntityType.DEVICES
    conditions: ConditionGroupRequest
    actions: List[ActionConfigRequest] = []
    schedule_enabled: bool = False
    schedule_cron: Optional[str] = None


class NLRuleRequest(BaseModel):
    """Request to create rule from natural language."""
    natural_language: str = Field(..., min_length=10)
    name: Optional[str] = None


class RuleResponse(BaseModel):
    """Rule response model."""
    id: str
    name: str
    description: Optional[str]
    entity_type: str
    conditions: dict
    actions: list
    schedule_enabled: bool
    schedule_cron: Optional[str]
    is_active: bool
    created_at: str
    
    class Config:
        from_attributes = True


class ParsedRuleResponse(BaseModel):
    """Response for NL parsing."""
    conditions: dict
    entity_type: str
    confidence: float
    suggested_name: Optional[str] = None


class QueryPreviewResponse(BaseModel):
    """Preview of generated SQL query."""
    sql: str
    estimated_count: Optional[int] = None


# Dependency for database session
async def get_db() -> AsyncSession:
    """Get database session."""
    # Implementation depends on your setup
    pass


# Routes
@router.get("", response_model=List[RuleResponse])
async def list_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    entity_type: Optional[EntityType] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """List all rules with optional filtering."""
    query = select(Rule).where(Rule.is_deleted == False)
    
    if entity_type:
        query = query.where(Rule.entity_type == entity_type)
    
    if active_only:
        query = query.where(Rule.is_active == True)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    rules = result.scalars().all()
    
    return [RuleResponse.from_orm(r) for r in rules]


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    request: CreateRuleRequest,
    db: AsyncSession = Depends(get_db),
    # current_user = Depends(get_current_user),
):
    """Create a new rule."""
    # Convert request to model
    rule = Rule(
        id=str(uuid4()),
        name=request.name,
        description=request.description,
        entity_type=request.entity_type,
        conditions=request.conditions.model_dump(),
        actions=[a.model_dump() for a in request.actions],
        schedule_enabled=request.schedule_enabled,
        schedule_cron=request.schedule_cron,
        created_by_id="system",  # Replace with current_user.id
    )
    
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    return RuleResponse.from_orm(rule)


@router.post("/parse-nl", response_model=ParsedRuleResponse)
async def parse_natural_language_rule(
    request: NLRuleRequest,
):
    """
    Parse natural language into rule conditions.
    
    This uses regex-based parsing. For better results, use the LLM endpoint.
    """
    conditions, entity_type, confidence = parse_natural_language(
        request.natural_language
    )
    
    # Generate suggested name if not provided
    suggested_name = request.name
    if not suggested_name:
        # Simple name generation
        words = request.natural_language.split()[:5]
        suggested_name = "_".join(words).replace(" ", "_")[:50]
    
    return ParsedRuleResponse(
        conditions=conditions.model_dump(),
        entity_type=entity_type.value,
        confidence=confidence,
        suggested_name=suggested_name,
    )


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific rule by ID."""
    result = await db.execute(
        select(Rule).where(Rule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found",
        )
    
    return RuleResponse.from_orm(rule)


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: str,
    request: CreateRuleRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing rule."""
    result = await db.execute(
        select(Rule).where(Rule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found",
        )
    
    # Update fields
    rule.name = request.name
    rule.description = request.description
    rule.entity_type = request.entity_type
    rule.conditions = request.conditions.model_dump()
    rule.actions = [a.model_dump() for a in request.actions]
    rule.schedule_enabled = request.schedule_enabled
    rule.schedule_cron = request.schedule_cron
    
    await db.commit()
    await db.refresh(rule)
    
    return RuleResponse.from_orm(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a rule."""
    result = await db.execute(
        select(Rule).where(Rule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found",
        )
    
    rule.is_deleted = True
    await db.commit()


@router.post("/{rule_id}/preview-query", response_model=QueryPreviewResponse)
async def preview_rule_query(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Preview the SQL query that would be generated for a rule."""
    result = await db.execute(
        select(Rule).where(Rule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found",
        )
    
    # Build query
    rule_def = RuleDefinition(
        name=rule.name,
        entity_type=rule.entity_type,
        conditions=ConditionGroup(**rule.conditions),
    )
    
    builder = QueryBuilder(rule_def)
    
    if rule.entity_type == EntityType.DEVICES:
        sql, _ = builder.build_device_query(limit=100)
    else:
        sql, _ = builder.build_application_query(limit=100)
    
    return QueryPreviewResponse(sql=sql)


@router.get("/templates", response_model=List[dict])
async def list_rule_templates(
    category: Optional[str] = None,
    entity_type: Optional[EntityType] = None,
    db: AsyncSession = Depends(get_db),
):
    """List available rule templates."""
    query = select(RuleTemplate)
    
    if category:
        query = query.where(RuleTemplate.category == category)
    
    if entity_type:
        query = query.where(RuleTemplate.entity_type == entity_type)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "category": t.category,
            "entity_type": t.entity_type.value,
            "conditions": t.conditions,
            "suggested_actions": t.suggested_actions,
        }
        for t in templates
    ]
```

---

## Verification

### Test the Rule Engine

```python
# Test query builder
from core_service.models.rule_conditions import (
    RuleDefinition, ConditionGroup, Condition, Operator, EntityType
)
from core_service.services.query_builder import QueryBuilder

# Create a test rule
rule = RuleDefinition(
    name="Low Disk Space Test",
    entity_type=EntityType.DEVICES,
    conditions=ConditionGroup(
        logic="AND",
        conditions=[
            Condition(field="free_disk_gb", operator=Operator.LESS_THAN, value=10),
            Condition(field="operating_system", operator=Operator.CONTAINS, value="Windows"),
        ]
    )
)

# Build query
builder = QueryBuilder(rule)
sql, params = builder.build_device_query()

print("Generated SQL:")
print(sql)
print("\nParameters:", params)
```

---

## Common Issues

### Issue: Field not found in mapping

**Solution:** Add the field to DEVICE_FIELD_MAPPING or APPLICATION_FIELD_MAPPING in query_builder.py

### Issue: SQL syntax errors

**Solution:** Test queries directly against MECM database before using in application

---

## Next Steps

→ [06_MECM_Connector.md](06_MECM_Connector.md) - Implement MECM database connector

---

**Checkpoint:** You should now have:
- [ ] Condition models defined (Operator, Condition, ConditionGroup)
- [ ] QueryBuilder converting rules to SQL
- [ ] ScanEngine executing scans
- [ ] NL parser for basic rule creation
- [ ] Rule API endpoints working
