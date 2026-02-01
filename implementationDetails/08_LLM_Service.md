# 08 - LLM Service Implementation Guide

## Overview

This guide covers implementing the LLM (Large Language Model) service for AI-powered features including natural language rule creation, remediation suggestions, and issue explanations.

---

## Prerequisites

- Core service API complete (see [04_Core_Service_API.md](04_Core_Service_API.md))
- OpenAI API key or Azure OpenAI access
- Redis for caching (optional but recommended)

---

## Step 1: LLM Provider Abstraction

📝 **PROMPT: Create LLM provider abstraction layer**
```
Create an abstract LLM provider interface with concrete implementations for:
- OpenAI (GPT-4)
- Azure OpenAI
- Local QWEN model
Include configuration for model selection, temperature, max tokens, and retry logic.
Use LangChain for standardized interface.
```

**File: `services/llm-service/src/llm_service/providers.py`**

```python
"""LLM provider implementations."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from langchain_core.language_models import BaseLLM
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from pydantic import BaseModel
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from llm_service.config import get_settings


class LLMProviderType(str, Enum):
    """Available LLM providers."""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    QWEN_LOCAL = "qwen_local"


class LLMConfig(BaseModel):
    """LLM configuration."""
    provider: LLMProviderType = LLMProviderType.OPENAI
    model: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: int = 2000
    timeout: int = 60


class LLMProvider(ABC):
    """Abstract LLM provider interface."""
    
    @abstractmethod
    def get_llm(self) -> BaseLLM:
        """Get the LangChain LLM instance."""
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.settings = get_settings()
        self.config = config or LLMConfig()
        self._llm: Optional[ChatOpenAI] = None
    
    def get_llm(self) -> ChatOpenAI:
        """Get ChatOpenAI instance."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                api_key=self.settings.openai_api_key,
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout,
            )
        return self._llm
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate response using OpenAI."""
        llm = self.get_llm()
        
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        response = await llm.ainvoke(messages, **kwargs)
        return response.content
    
    def is_available(self) -> bool:
        """Check if OpenAI is configured."""
        return bool(self.settings.openai_api_key)


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI provider."""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.settings = get_settings()
        self.config = config or LLMConfig()
        self._llm: Optional[AzureChatOpenAI] = None
    
    def get_llm(self) -> AzureChatOpenAI:
        """Get AzureChatOpenAI instance."""
        if self._llm is None:
            self._llm = AzureChatOpenAI(
                azure_endpoint=self.settings.azure_openai_endpoint,
                api_key=self.settings.azure_openai_api_key,
                azure_deployment=self.settings.azure_openai_deployment,
                api_version="2024-02-01",
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
        return self._llm
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate response using Azure OpenAI."""
        llm = self.get_llm()
        
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        response = await llm.ainvoke(messages, **kwargs)
        return response.content
    
    def is_available(self) -> bool:
        """Check if Azure OpenAI is configured."""
        return all([
            self.settings.azure_openai_api_key,
            self.settings.azure_openai_endpoint,
            self.settings.azure_openai_deployment,
        ])


class QWENLocalProvider(LLMProvider):
    """Local QWEN model provider (for air-gapped environments)."""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.settings = get_settings()
        self.config = config or LLMConfig(model="qwen-7b-chat")
        self.base_url = self.settings.qwen_api_url or "http://localhost:8000"
    
    def get_llm(self) -> BaseLLM:
        """Get LLM instance - QWEN uses custom API."""
        raise NotImplementedError("QWEN uses custom API, use generate() directly")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate response using local QWEN model."""
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            payload = {
                "prompt": prompt,
                "system": system_prompt or "",
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            }
            
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def is_available(self) -> bool:
        """Check if QWEN server is reachable."""
        try:
            import httpx
            response = httpx.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False


class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    _providers: Dict[LLMProviderType, type] = {
        LLMProviderType.OPENAI: OpenAIProvider,
        LLMProviderType.AZURE_OPENAI: AzureOpenAIProvider,
        LLMProviderType.QWEN_LOCAL: QWENLocalProvider,
    }
    
    @classmethod
    def create(
        cls,
        provider_type: LLMProviderType,
        config: Optional[LLMConfig] = None
    ) -> LLMProvider:
        """Create an LLM provider instance."""
        provider_class = cls._providers.get(provider_type)
        if not provider_class:
            raise ValueError(f"Unknown provider type: {provider_type}")
        return provider_class(config)
    
    @classmethod
    def get_available_provider(cls) -> Optional[LLMProvider]:
        """Get the first available provider."""
        for provider_type in cls._providers:
            provider = cls.create(provider_type)
            if provider.is_available():
                return provider
        return None
```

---

## Step 2: Sensitive Data Filter

📝 **PROMPT: Create PII/sensitive data filter**
```
Create a SensitiveDataFilter class that:
- Detects and masks PII (emails, IPs, hostnames, serial numbers)
- Maintains a mapping for de-anonymization if needed
- Works bidirectionally (mask before sending to LLM, unmask in response)
- Is configurable for different data types
```

**File: `services/llm-service/src/llm_service/data_filter.py`**

```python
"""Sensitive data filtering for LLM interactions."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Pattern, Tuple


@dataclass
class FilterRule:
    """Rule for detecting and masking sensitive data."""
    name: str
    pattern: Pattern
    replacement_template: str
    description: str


@dataclass
class FilterMapping:
    """Mapping of original values to masked values."""
    mappings: Dict[str, str] = field(default_factory=dict)
    reverse_mappings: Dict[str, str] = field(default_factory=dict)
    counters: Dict[str, int] = field(default_factory=lambda: {})
    
    def add(self, rule_name: str, original: str) -> str:
        """Add a mapping and return the masked value."""
        if original in self.mappings:
            return self.mappings[original]
        
        # Increment counter for this rule type
        self.counters.setdefault(rule_name, 0)
        self.counters[rule_name] += 1
        
        # Create masked value
        masked = f"[{rule_name.upper()}_{self.counters[rule_name]}]"
        
        self.mappings[original] = masked
        self.reverse_mappings[masked] = original
        
        return masked
    
    def unmask(self, text: str) -> str:
        """Replace masked values with originals."""
        result = text
        for masked, original in self.reverse_mappings.items():
            result = result.replace(masked, original)
        return result


class SensitiveDataFilter:
    """Filter sensitive data before sending to LLM."""
    
    # Default filter rules
    DEFAULT_RULES = [
        FilterRule(
            name="email",
            pattern=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            replacement_template="[EMAIL_{n}]",
            description="Email addresses"
        ),
        FilterRule(
            name="ip_v4",
            pattern=re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'),
            replacement_template="[IP_{n}]",
            description="IPv4 addresses"
        ),
        FilterRule(
            name="hostname",
            pattern=re.compile(r'\b(?:WS|PC|SRV|DESKTOP|LAPTOP|VM|DC|FS|WEB|APP|DB)-[A-Z0-9]{2,}(?:-[A-Z0-9]+)*\b', re.IGNORECASE),
            replacement_template="[DEVICE_{n}]",
            description="Windows hostnames"
        ),
        FilterRule(
            name="serial",
            pattern=re.compile(r'\b[A-Z0-9]{8,}(?:-[A-Z0-9]+)*\b'),
            replacement_template="[SERIAL_{n}]",
            description="Serial numbers"
        ),
        FilterRule(
            name="mac_address",
            pattern=re.compile(r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b'),
            replacement_template="[MAC_{n}]",
            description="MAC addresses"
        ),
        FilterRule(
            name="username",
            pattern=re.compile(r'\b(?:DOMAIN\\)?[a-z]{2,}\.[a-z]{2,}[0-9]*\b', re.IGNORECASE),
            replacement_template="[USER_{n}]",
            description="Usernames (firstname.lastname format)"
        ),
        FilterRule(
            name="phone",
            pattern=re.compile(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'),
            replacement_template="[PHONE_{n}]",
            description="Phone numbers"
        ),
    ]
    
    def __init__(self, rules: Optional[List[FilterRule]] = None):
        self.rules = rules or self.DEFAULT_RULES
    
    def filter_text(self, text: str) -> Tuple[str, FilterMapping]:
        """
        Filter sensitive data from text.
        
        Args:
            text: Input text containing sensitive data
            
        Returns:
            Tuple of (filtered text, mapping for de-anonymization)
        """
        mapping = FilterMapping()
        filtered = text
        
        for rule in self.rules:
            matches = rule.pattern.findall(filtered)
            for match in matches:
                masked = mapping.add(rule.name, match)
                filtered = filtered.replace(match, masked, 1)
        
        return filtered, mapping
    
    def filter_dict(
        self, 
        data: Dict, 
        keys_to_filter: Optional[List[str]] = None
    ) -> Tuple[Dict, FilterMapping]:
        """
        Filter sensitive data from dictionary values.
        
        Args:
            data: Dictionary with potentially sensitive values
            keys_to_filter: Specific keys to filter (None = all string values)
            
        Returns:
            Tuple of (filtered dict, mapping)
        """
        mapping = FilterMapping()
        filtered_data = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                if keys_to_filter is None or key in keys_to_filter:
                    filtered_value, key_mapping = self.filter_text(value)
                    # Merge mappings
                    mapping.mappings.update(key_mapping.mappings)
                    mapping.reverse_mappings.update(key_mapping.reverse_mappings)
                    filtered_data[key] = filtered_value
                else:
                    filtered_data[key] = value
            elif isinstance(value, dict):
                filtered_data[key], nested_mapping = self.filter_dict(value, keys_to_filter)
                mapping.mappings.update(nested_mapping.mappings)
                mapping.reverse_mappings.update(nested_mapping.reverse_mappings)
            elif isinstance(value, list):
                filtered_data[key] = []
                for item in value:
                    if isinstance(item, str):
                        filtered_item, item_mapping = self.filter_text(item)
                        mapping.mappings.update(item_mapping.mappings)
                        mapping.reverse_mappings.update(item_mapping.reverse_mappings)
                        filtered_data[key].append(filtered_item)
                    elif isinstance(item, dict):
                        filtered_item, item_mapping = self.filter_dict(item, keys_to_filter)
                        mapping.mappings.update(item_mapping.mappings)
                        mapping.reverse_mappings.update(item_mapping.reverse_mappings)
                        filtered_data[key].append(filtered_item)
                    else:
                        filtered_data[key].append(item)
            else:
                filtered_data[key] = value
        
        return filtered_data, mapping
    
    def unmask_text(self, text: str, mapping: FilterMapping) -> str:
        """
        Restore original values in text.
        
        Args:
            text: Text with masked values
            mapping: Mapping from filter_text()
            
        Returns:
            Text with original values restored
        """
        return mapping.unmask(text)


# Convenience instance
default_filter = SensitiveDataFilter()
```

---

## Step 3: Prompt Templates

📝 **PROMPT: Create prompt templates for AI features**
```
Create structured prompt templates for:
1. Natural language to rule conversion
2. Remediation suggestions based on scan results
3. Issue explanation for end users
4. Scan results summarization
Use Jinja2 or f-string templates with clear instructions.
```

**File: `services/llm-service/src/llm_service/prompts.py`**

```python
"""Prompt templates for LLM interactions."""

from typing import Any, Dict, List, Optional
from string import Template


class PromptTemplates:
    """Collection of prompt templates for AI features."""
    
    # System prompts
    SYSTEM_RULE_BUILDER = """You are an IT operations assistant helping to create rules for identifying problematic devices and applications.

Your task is to convert natural language descriptions into structured rule conditions.

Available fields for DEVICES:
- device_name (string): Computer hostname
- operating_system (string): OS name like "Windows 10", "Windows 11"
- free_disk_gb (number): Free disk space in gigabytes
- last_active_days (number): Days since device was last seen
- missing_critical_patches (number): Count of missing security patches
- manufacturer (string): Hardware manufacturer
- model (string): Hardware model

Available fields for APPLICATIONS:
- app_name (string): Application name
- app_version (string): Version number
- publisher (string): Software publisher
- install_count (number): Number of installations
- cve_count (number): Number of vulnerabilities

Available operators:
- eq (equals)
- neq (not equals)
- gt (greater than)
- lt (less than)
- gte (greater than or equal)
- lte (less than or equal)
- contains (string contains)
- starts_with
- ends_with
- in (value in list)
- older_than_days (for dates)
- newer_than_days (for dates)

Respond ONLY with valid JSON in this format:
{
    "entity_type": "devices" or "applications" or "both",
    "conditions": {
        "logic": "AND" or "OR",
        "conditions": [
            {"field": "field_name", "operator": "operator", "value": value}
        ]
    },
    "suggested_name": "Short descriptive name",
    "confidence": 0.0-1.0
}"""

    SYSTEM_REMEDIATION = """You are an IT operations expert providing remediation suggestions.

Given scan results showing problematic devices or applications, suggest appropriate remediation actions.

Available action types:
- create_collection: Create an MECM collection with affected devices
- create_deployment: Create a software deployment to fix issues
- create_incident: Create a ServiceNow incident ticket
- notify_app_owner: Send notification to application owner
- run_tachyon_instruction: Execute a Tachyon instruction on devices

Consider:
1. Urgency based on severity and count
2. Grouping similar issues together
3. Least disruptive solutions first
4. Compliance requirements

Respond with JSON containing suggested actions with reasoning."""

    SYSTEM_EXPLANATION = """You are an IT support assistant explaining technical issues in plain language.

Given device or application information and the issues found, explain:
1. What the issue is in non-technical terms
2. Why it matters (security, performance, compliance)
3. What will happen if not addressed
4. Recommended next steps

Keep explanations clear and concise. Avoid jargon."""

    # User prompt templates
    RULE_FROM_NL = Template("""Convert this natural language description into a structured rule:

"$description"

Remember to:
1. Identify the entity type (devices, applications, or both)
2. Extract all conditions mentioned
3. Choose appropriate operators
4. Combine with AND/OR logic as implied
5. Provide a confidence score

Respond with JSON only.""")

    REMEDIATION_SUGGESTION = Template("""Analyze these scan results and suggest remediation actions:

Rule: $rule_name
Entity Type: $entity_type
Total Matches: $total_matches

Results Summary:
$results_summary

Severity Breakdown:
- Critical: $critical_count
- High: $high_count
- Medium: $medium_count
- Low: $low_count

Suggest appropriate actions considering:
1. The number of affected entities
2. The severity distribution
3. Grouping opportunities
4. Business impact

Respond with JSON containing:
{
    "suggested_actions": [
        {
            "action_type": "type",
            "priority": 1-5,
            "reason": "explanation",
            "params": {}
        }
    ],
    "summary": "brief summary of recommendations",
    "risk_assessment": "overall risk level"
}""")

    ISSUE_EXPLANATION = Template("""Explain this IT issue in plain language:

Entity: $entity_name ($entity_type)
Issue Type: $issue_type

Technical Details:
$technical_details

Conditions Matched:
$matched_conditions

Create a clear explanation including:
1. What's wrong (in simple terms)
2. Why this matters
3. Potential impact if not fixed
4. Recommended action

Keep it under 200 words.""")

    SCAN_SUMMARY = Template("""Summarize these scan results for a management report:

Rule: $rule_name
Scan Date: $scan_date
Duration: $duration

Results:
- Total Scanned: $total_scanned
- Total Matched: $total_matched
- Match Rate: $match_rate%

By Severity:
$severity_breakdown

Top Issues:
$top_issues

Provide:
1. Executive summary (2-3 sentences)
2. Key findings (bullet points)
3. Risk assessment
4. Recommended priorities""")


class PromptBuilder:
    """Build prompts from templates with data."""
    
    def __init__(self):
        self.templates = PromptTemplates()
    
    def build_rule_prompt(self, description: str) -> tuple[str, str]:
        """Build prompt for rule creation from NL."""
        system = self.templates.SYSTEM_RULE_BUILDER
        user = self.templates.RULE_FROM_NL.substitute(description=description)
        return system, user
    
    def build_remediation_prompt(
        self,
        rule_name: str,
        entity_type: str,
        results: List[Dict[str, Any]],
    ) -> tuple[str, str]:
        """Build prompt for remediation suggestions."""
        # Summarize results
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for r in results:
            severity = r.get("severity", "medium").lower()
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Create summary
        summary_lines = []
        for r in results[:10]:  # Top 10 for context
            summary_lines.append(f"- {r.get('entity_name')}: {r.get('severity', 'medium')}")
        
        system = self.templates.SYSTEM_REMEDIATION
        user = self.templates.REMEDIATION_SUGGESTION.substitute(
            rule_name=rule_name,
            entity_type=entity_type,
            total_matches=len(results),
            results_summary="\n".join(summary_lines),
            critical_count=severity_counts["critical"],
            high_count=severity_counts["high"],
            medium_count=severity_counts["medium"],
            low_count=severity_counts["low"],
        )
        
        return system, user
    
    def build_explanation_prompt(
        self,
        entity_name: str,
        entity_type: str,
        issue_type: str,
        technical_details: Dict[str, Any],
        matched_conditions: List[str],
    ) -> tuple[str, str]:
        """Build prompt for issue explanation."""
        system = self.templates.SYSTEM_EXPLANATION
        user = self.templates.ISSUE_EXPLANATION.substitute(
            entity_name=entity_name,
            entity_type=entity_type,
            issue_type=issue_type,
            technical_details="\n".join(f"- {k}: {v}" for k, v in technical_details.items()),
            matched_conditions="\n".join(f"- {c}" for c in matched_conditions),
        )
        
        return system, user
    
    def build_summary_prompt(
        self,
        rule_name: str,
        scan_date: str,
        duration: str,
        stats: Dict[str, Any],
        severity_breakdown: Dict[str, int],
        top_issues: List[str],
    ) -> tuple[str, str]:
        """Build prompt for scan summary."""
        system = "You are an IT operations analyst creating management reports."
        
        severity_lines = "\n".join(
            f"- {sev.title()}: {count}" 
            for sev, count in severity_breakdown.items()
        )
        
        match_rate = 0
        if stats.get("total_scanned", 0) > 0:
            match_rate = (stats.get("total_matched", 0) / stats["total_scanned"]) * 100
        
        user = self.templates.SCAN_SUMMARY.substitute(
            rule_name=rule_name,
            scan_date=scan_date,
            duration=duration,
            total_scanned=stats.get("total_scanned", 0),
            total_matched=stats.get("total_matched", 0),
            match_rate=f"{match_rate:.1f}",
            severity_breakdown=severity_lines,
            top_issues="\n".join(f"- {issue}" for issue in top_issues),
        )
        
        return system, user
```

---

## Step 4: LLM Service Implementation

**File: `services/llm-service/src/llm_service/service.py`**

```python
"""LLM service for AI-powered features."""

import json
from typing import Any, Dict, List, Optional
import structlog

from llm_service.config import get_settings
from llm_service.providers import LLMProvider, LLMProviderFactory, LLMProviderType, LLMConfig
from llm_service.data_filter import SensitiveDataFilter, FilterMapping
from llm_service.prompts import PromptBuilder

logger = structlog.get_logger()


class LLMService:
    """Main LLM service for AI features."""
    
    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        data_filter: Optional[SensitiveDataFilter] = None,
    ):
        self.settings = get_settings()
        self.provider = provider or LLMProviderFactory.get_available_provider()
        self.filter = data_filter or SensitiveDataFilter()
        self.prompt_builder = PromptBuilder()
        
        if not self.provider:
            raise RuntimeError("No LLM provider available")
    
    async def interpret_rule(
        self,
        natural_language: str,
    ) -> Dict[str, Any]:
        """
        Convert natural language to structured rule conditions.
        
        Args:
            natural_language: Plain English rule description
            
        Returns:
            Dict with entity_type, conditions, suggested_name, confidence
        """
        # Filter sensitive data
        filtered_text, mapping = self.filter.filter_text(natural_language)
        
        # Build prompt
        system, user = self.prompt_builder.build_rule_prompt(filtered_text)
        
        # Generate response
        response = await self.provider.generate(user, system_prompt=system)
        
        # Parse JSON response
        try:
            result = json.loads(response)
            
            # Unmask any sensitive data in result
            if "suggested_name" in result:
                result["suggested_name"] = mapping.unmask(result["suggested_name"])
            
            logger.info(
                "Rule interpreted",
                entity_type=result.get("entity_type"),
                confidence=result.get("confidence"),
            )
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response", error=str(e), response=response)
            raise ValueError(f"Invalid LLM response: {e}")
    
    async def suggest_remediation(
        self,
        rule_name: str,
        entity_type: str,
        results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Suggest remediation actions for scan results.
        
        Args:
            rule_name: Name of the rule that was executed
            entity_type: Type of entities (devices/applications)
            results: List of scan result dictionaries
            
        Returns:
            Dict with suggested_actions, summary, risk_assessment
        """
        # Filter sensitive data from results
        filtered_results, mapping = self.filter.filter_dict({"results": results})
        
        # Build prompt
        system, user = self.prompt_builder.build_remediation_prompt(
            rule_name=rule_name,
            entity_type=entity_type,
            results=filtered_results["results"],
        )
        
        # Generate response
        response = await self.provider.generate(user, system_prompt=system)
        
        # Parse and unmask
        try:
            result = json.loads(response)
            
            # Unmask sensitive data in result
            result["summary"] = mapping.unmask(result.get("summary", ""))
            
            logger.info(
                "Remediation suggested",
                action_count=len(result.get("suggested_actions", [])),
                risk=result.get("risk_assessment"),
            )
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse remediation response", error=str(e))
            raise ValueError(f"Invalid LLM response: {e}")
    
    async def explain_issue(
        self,
        entity_name: str,
        entity_type: str,
        issue_type: str,
        technical_details: Dict[str, Any],
        matched_conditions: List[str],
    ) -> str:
        """
        Generate plain-language explanation of an issue.
        
        Args:
            entity_name: Name of the device/application
            entity_type: Type of entity
            issue_type: Category of issue
            technical_details: Technical data about the issue
            matched_conditions: Conditions that triggered the match
            
        Returns:
            Plain-language explanation string
        """
        # Filter sensitive data
        filtered_name, name_mapping = self.filter.filter_text(entity_name)
        filtered_details, details_mapping = self.filter.filter_dict(technical_details)
        
        # Build prompt
        system, user = self.prompt_builder.build_explanation_prompt(
            entity_name=filtered_name,
            entity_type=entity_type,
            issue_type=issue_type,
            technical_details=filtered_details,
            matched_conditions=matched_conditions,
        )
        
        # Generate response
        response = await self.provider.generate(user, system_prompt=system)
        
        # Unmask sensitive data in response
        response = name_mapping.unmask(response)
        response = details_mapping.unmask(response)
        
        return response
    
    async def summarize_scan(
        self,
        rule_name: str,
        scan_date: str,
        duration: str,
        stats: Dict[str, Any],
        severity_breakdown: Dict[str, int],
        top_issues: List[str],
    ) -> str:
        """
        Generate executive summary of scan results.
        
        Args:
            rule_name: Name of the rule
            scan_date: When the scan ran
            duration: How long the scan took
            stats: Scan statistics
            severity_breakdown: Count by severity
            top_issues: List of top issues found
            
        Returns:
            Executive summary text
        """
        # Build prompt
        system, user = self.prompt_builder.build_summary_prompt(
            rule_name=rule_name,
            scan_date=scan_date,
            duration=duration,
            stats=stats,
            severity_breakdown=severity_breakdown,
            top_issues=top_issues,
        )
        
        # Generate response
        response = await self.provider.generate(user, system_prompt=system)
        
        return response
    
    async def validate_rule_conditions(
        self,
        conditions: Dict[str, Any],
        entity_type: str,
    ) -> Dict[str, Any]:
        """
        Use LLM to validate and improve rule conditions.
        
        Returns suggestions for improvement if any.
        """
        prompt = f"""Review these rule conditions for an IT operations tool:

Entity Type: {entity_type}
Conditions: {json.dumps(conditions, indent=2)}

Check for:
1. Logical errors or contradictions
2. Missing common related conditions
3. Overly broad or narrow criteria
4. Best practice suggestions

Respond with JSON:
{{
    "is_valid": true/false,
    "issues": ["list of issues if any"],
    "suggestions": ["list of improvement suggestions"],
    "improved_conditions": null or improved version
}}"""

        response = await self.provider.generate(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"is_valid": True, "issues": [], "suggestions": []}
```

---

## Step 5: LLM API Routes

**File: `services/llm-service/src/llm_service/routes.py`**

```python
"""LLM service API routes."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from llm_service.service import LLMService
from llm_service.providers import LLMProviderType, LLMConfig

router = APIRouter(prefix="/api/llm", tags=["LLM"])


# Request/Response Models
class InterpretRuleRequest(BaseModel):
    """Request to interpret natural language rule."""
    natural_language: str = Field(..., min_length=10, max_length=1000)


class InterpretRuleResponse(BaseModel):
    """Response from rule interpretation."""
    entity_type: str
    conditions: Dict[str, Any]
    suggested_name: Optional[str] = None
    confidence: float


class RemediationRequest(BaseModel):
    """Request for remediation suggestions."""
    rule_name: str
    entity_type: str
    results: List[Dict[str, Any]]


class RemediationResponse(BaseModel):
    """Remediation suggestion response."""
    suggested_actions: List[Dict[str, Any]]
    summary: str
    risk_assessment: str


class ExplainIssueRequest(BaseModel):
    """Request to explain an issue."""
    entity_name: str
    entity_type: str
    issue_type: str
    technical_details: Dict[str, Any]
    matched_conditions: List[str]


class ProviderStatusResponse(BaseModel):
    """LLM provider status."""
    provider: str
    available: bool
    model: Optional[str] = None


class UpdateConfigRequest(BaseModel):
    """Request to update LLM configuration."""
    provider: Optional[LLMProviderType] = None
    model: Optional[str] = None
    temperature: Optional[float] = None


# Dependency
def get_llm_service() -> LLMService:
    """Get LLM service instance."""
    return LLMService()


# Routes
@router.post("/interpret-rule", response_model=InterpretRuleResponse)
async def interpret_rule(
    request: InterpretRuleRequest,
    service: LLMService = Depends(get_llm_service),
):
    """
    Convert natural language description to structured rule conditions.
    
    Example input: "Find devices with less than 10GB free disk space 
    that haven't been patched in the last 30 days"
    """
    try:
        result = await service.interpret_rule(request.natural_language)
        return InterpretRuleResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM service error: {str(e)}"
        )


@router.post("/suggest-remediation", response_model=RemediationResponse)
async def suggest_remediation(
    request: RemediationRequest,
    service: LLMService = Depends(get_llm_service),
):
    """
    Get AI-suggested remediation actions for scan results.
    """
    try:
        result = await service.suggest_remediation(
            rule_name=request.rule_name,
            entity_type=request.entity_type,
            results=request.results,
        )
        return RemediationResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.post("/explain-issue")
async def explain_issue(
    request: ExplainIssueRequest,
    service: LLMService = Depends(get_llm_service),
):
    """
    Get plain-language explanation of a device/application issue.
    """
    try:
        explanation = await service.explain_issue(
            entity_name=request.entity_name,
            entity_type=request.entity_type,
            issue_type=request.issue_type,
            technical_details=request.technical_details,
            matched_conditions=request.matched_conditions,
        )
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/providers", response_model=List[ProviderStatusResponse])
async def list_providers():
    """
    List available LLM providers and their status.
    """
    from llm_service.providers import LLMProviderFactory, LLMProviderType
    
    statuses = []
    for provider_type in LLMProviderType:
        try:
            provider = LLMProviderFactory.create(provider_type)
            statuses.append(ProviderStatusResponse(
                provider=provider_type.value,
                available=provider.is_available(),
                model=getattr(provider, 'config', LLMConfig()).model,
            ))
        except Exception:
            statuses.append(ProviderStatusResponse(
                provider=provider_type.value,
                available=False,
            ))
    
    return statuses


@router.put("/config")
async def update_config(request: UpdateConfigRequest):
    """
    Update LLM configuration (admin only).
    """
    # This would update application state or database
    # Implementation depends on your config management approach
    return {"status": "updated", "config": request.model_dump(exclude_none=True)}


@router.get("/health")
async def health_check():
    """Health check for LLM service."""
    from llm_service.providers import LLMProviderFactory
    
    provider = LLMProviderFactory.get_available_provider()
    
    return {
        "status": "healthy" if provider else "degraded",
        "provider_available": provider is not None,
    }
```

---

## Step 6: Unit Tests

**File: `tests/unit/test_llm_service.py`**

```python
"""Unit tests for LLM service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from llm_service.data_filter import SensitiveDataFilter, FilterMapping
from llm_service.prompts import PromptBuilder
from llm_service.providers import OpenAIProvider, LLMConfig


class TestSensitiveDataFilter:
    """Tests for data filtering."""
    
    def test_filter_email(self):
        """Test email address filtering."""
        filter = SensitiveDataFilter()
        text = "Contact john.doe@company.com for support"
        
        filtered, mapping = filter.filter_text(text)
        
        assert "john.doe@company.com" not in filtered
        assert "[EMAIL_1]" in filtered
        assert mapping.mappings["john.doe@company.com"] == "[EMAIL_1]"
    
    def test_filter_ip_address(self):
        """Test IP address filtering."""
        filter = SensitiveDataFilter()
        text = "Server at 192.168.1.100 is down"
        
        filtered, mapping = filter.filter_text(text)
        
        assert "192.168.1.100" not in filtered
        assert "[IP_1]" in filtered
    
    def test_filter_hostname(self):
        """Test hostname filtering."""
        filter = SensitiveDataFilter()
        text = "Device WS-NYC-12345 has low disk space"
        
        filtered, mapping = filter.filter_text(text)
        
        assert "WS-NYC-12345" not in filtered
        assert "[DEVICE_1]" in filtered
    
    def test_unmask_text(self):
        """Test unmasking filtered text."""
        filter = SensitiveDataFilter()
        original = "Contact john@company.com about WS-NYC-001"
        
        filtered, mapping = filter.filter_text(original)
        unmasked = filter.unmask_text(filtered, mapping)
        
        assert unmasked == original
    
    def test_filter_dict(self):
        """Test filtering dictionary values."""
        filter = SensitiveDataFilter()
        data = {
            "name": "WS-NYC-12345",
            "user": "john.doe@company.com",
            "ip": "10.0.0.1",
            "count": 42,  # Should not be filtered
        }
        
        filtered, mapping = filter.filter_dict(data)
        
        assert "[DEVICE_1]" in filtered["name"]
        assert "[EMAIL_1]" in filtered["user"]
        assert filtered["count"] == 42


class TestPromptBuilder:
    """Tests for prompt building."""
    
    def test_build_rule_prompt(self):
        """Test rule creation prompt."""
        builder = PromptBuilder()
        
        system, user = builder.build_rule_prompt(
            "Find devices with less than 10GB disk space"
        )
        
        assert "DEVICES" in system or "devices" in system
        assert "10GB" in user or "10 GB" in user
    
    def test_build_remediation_prompt(self):
        """Test remediation prompt."""
        builder = PromptBuilder()
        results = [
            {"entity_name": "Device1", "severity": "high"},
            {"entity_name": "Device2", "severity": "critical"},
        ]
        
        system, user = builder.build_remediation_prompt(
            rule_name="Low Disk Space",
            entity_type="devices",
            results=results,
        )
        
        assert "Low Disk Space" in user
        assert "2" in user  # Total matches


class TestLLMProviders:
    """Tests for LLM providers."""
    
    def test_openai_provider_not_available_without_key(self):
        """Test OpenAI provider availability check."""
        with patch('llm_service.providers.get_settings') as mock_settings:
            mock_settings.return_value.openai_api_key = ""
            
            provider = OpenAIProvider()
            assert not provider.is_available()
    
    @pytest.mark.asyncio
    async def test_generate_with_mock(self):
        """Test generate with mocked LLM."""
        with patch('llm_service.providers.get_settings') as mock_settings:
            mock_settings.return_value.openai_api_key = "test-key"
            
            provider = OpenAIProvider()
            
            # Mock the LLM
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value.content = '{"test": "response"}'
            provider._llm = mock_llm
            
            result = await provider.generate("test prompt")
            
            assert '{"test": "response"}' in result


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## Verification

### Test the LLM Service

```python
# Test interpretation
import asyncio
from llm_service.service import LLMService

async def test():
    service = LLMService()
    
    result = await service.interpret_rule(
        "Find Windows 10 devices with less than 10GB free disk space"
    )
    print(result)

asyncio.run(test())
```

### Test API Endpoints

```powershell
# Start service
uvicorn llm_service.main:app --reload --port 8003

# Test interpretation
curl -X POST http://localhost:8003/api/llm/interpret-rule \
  -H "Content-Type: application/json" \
  -d '{"natural_language": "Find devices with less than 10GB disk space"}'
```

---

## Common Issues

### Issue: OpenAI rate limiting

**Solution:** Implement exponential backoff (already in providers.py with tenacity)

### Issue: Sensitive data in LLM responses

**Solution:** Always unmask after receiving response using the FilterMapping

### Issue: JSON parsing errors from LLM

**Solution:** Add retry logic with different temperature or explicit JSON mode

---

## Next Steps

→ [09_Ground_Truth_Testing.md](09_Ground_Truth_Testing.md) - Implement AI validation testing

---

**Checkpoint:** You should now have:
- [ ] LLM provider abstraction with OpenAI/Azure/QWEN support
- [ ] Sensitive data filtering working
- [ ] Prompt templates for all AI features
- [ ] LLM service with interpret/suggest/explain methods
- [ ] API endpoints tested
- [ ] Unit tests passing
