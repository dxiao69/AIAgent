# 07 - Desktop Application Implementation Guide

## Overview

This guide covers implementing the PySide6 (Qt 6) desktop application with MVVM architecture. The app provides the primary user interface for rule management, scan execution, and result visualization.

---

## Prerequisites

- Core service API running (see [04_Core_Service_API.md](04_Core_Service_API.md))
- Python 3.11+ installed
- PySide6 6.5+ installed

---

## Step 1: Project Structure

📝 **PROMPT: Create desktop application project structure**
```
Create a PySide6 desktop application structure with:
- MVVM architecture (Models, Views, ViewModels)
- QSS stylesheets for theming
- Resource management for icons
- Configuration management
- HTTP client for API communication
```

**Directory Structure:**

```
desktop-app/
├── src/
│   └── it_ops_agent/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── client.py
│       │   └── auth.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── rule.py
│       │   ├── scan.py
│       │   └── device.py
│       ├── viewmodels/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── dashboard_vm.py
│       │   ├── rules_vm.py
│       │   ├── rule_builder_vm.py
│       │   ├── scans_vm.py
│       │   └── devices_vm.py
│       ├── views/
│       │   ├── __init__.py
│       │   ├── main_window.py
│       │   ├── dashboard.py
│       │   ├── rules_list.py
│       │   ├── rule_builder.py
│       │   ├── scan_results.py
│       │   └── components/
│       │       ├── __init__.py
│       │       ├── sidebar.py
│       │       ├── header.py
│       │       ├── data_table.py
│       │       └── charts.py
│       ├── resources/
│       │   ├── icons/
│       │   ├── styles/
│       │   │   └── dark_theme.qss
│       │   └── resources.qrc
│       └── utils/
│           ├── __init__.py
│           └── signals.py
├── tests/
├── requirements.txt
└── setup.py
```

---

## Step 2: Configuration

**File: `desktop-app/src/it_ops_agent/config.py`**

```python
"""Application configuration."""

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class AppConfig(BaseModel):
    """Application configuration."""
    
    # API settings
    api_base_url: str = "http://localhost:8001/api/v1"
    api_timeout: int = 30
    
    # UI settings
    theme: str = "dark"
    window_width: int = 1400
    window_height: int = 900
    sidebar_width: int = 240
    
    # Auth settings
    auth_server_url: str = "https://login.microsoftonline.com"
    client_id: str = ""
    tenant_id: str = ""
    
    # Feature flags
    enable_ai_features: bool = True
    enable_action_requests: bool = True


_config: Optional[AppConfig] = None
_config_path = Path.home() / ".it_ops_agent" / "config.json"


def get_config() -> AppConfig:
    """Get application configuration."""
    global _config
    
    if _config is None:
        _config = load_config()
    
    return _config


def load_config() -> AppConfig:
    """Load configuration from file."""
    if _config_path.exists():
        try:
            with open(_config_path) as f:
                data = json.load(f)
            return AppConfig(**data)
        except Exception:
            pass
    
    return AppConfig()


def save_config(config: AppConfig):
    """Save configuration to file."""
    global _config
    
    _config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(_config_path, "w") as f:
        json.dump(config.model_dump(), f, indent=2)
    
    _config = config
```

---

## Step 3: API Client

📝 **PROMPT: Create async HTTP client for backend API**
```
Create an API client class for the desktop app that:
- Uses httpx for async HTTP requests
- Handles JWT token refresh
- Provides typed methods for all API endpoints
- Implements retry logic for network errors
- Emits Qt signals for async completion
```

**File: `desktop-app/src/it_ops_agent/api/client.py`**

```python
"""API client for backend communication."""

from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
from PySide6.QtCore import QObject, Signal

from it_ops_agent.config import get_config


class ApiClient(QObject):
    """HTTP client for backend API."""
    
    # Signals for async operations
    request_started = Signal()
    request_finished = Signal()
    request_error = Signal(str)
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.config = get_config()
        self._token: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.api_base_url,
                timeout=self.config.api_timeout,
            )
        return self._client
    
    def set_token(self, token: str):
        """Set authentication token."""
        self._token = token
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    # Dashboard endpoints
    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary statistics."""
        self.request_started.emit()
        try:
            response = await self.client.get("/dashboard/summary", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.request_error.emit(str(e))
            raise
        finally:
            self.request_finished.emit()
    
    async def get_severity_trends(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get severity trends."""
        response = await self.client.get(
            "/dashboard/severity-trends",
            params={"days": days},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()
    
    async def get_recent_scans(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent scans."""
        response = await self.client.get(
            "/dashboard/recent-scans",
            params={"limit": limit},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()
    
    # Rules endpoints
    async def list_rules(
        self,
        search: Optional[str] = None,
        entity_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List rules with filtering."""
        params = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        if entity_type:
            params["entity_type"] = entity_type
        
        self.request_started.emit()
        try:
            response = await self.client.get("/rules", params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        finally:
            self.request_finished.emit()
    
    async def get_rule(self, rule_id: str) -> Dict[str, Any]:
        """Get single rule."""
        response = await self.client.get(f"/rules/{rule_id}", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    async def create_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new rule."""
        self.request_started.emit()
        try:
            response = await self.client.post("/rules", json=rule_data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            self.request_error.emit(f"Failed to create rule: {e.response.text}")
            raise
        finally:
            self.request_finished.emit()
    
    async def update_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a rule."""
        response = await self.client.put(f"/rules/{rule_id}", json=rule_data, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    async def delete_rule(self, rule_id: str):
        """Delete a rule."""
        response = await self.client.delete(f"/rules/{rule_id}", headers=self.headers)
        response.raise_for_status()
    
    async def clone_rule(self, rule_id: str, new_name: Optional[str] = None) -> Dict[str, Any]:
        """Clone a rule."""
        params = {}
        if new_name:
            params["new_name"] = new_name
        
        response = await self.client.post(
            f"/rules/{rule_id}/clone",
            params=params,
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()
    
    async def list_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List rule templates."""
        params = {}
        if category:
            params["category"] = category
        
        response = await self.client.get("/rules/templates", params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    # Scan endpoints
    async def list_scans(
        self,
        rule_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List scans."""
        params = {"page": page, "page_size": page_size}
        if rule_id:
            params["rule_id"] = rule_id
        if status:
            params["status"] = status
        
        response = await self.client.get("/scans", params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    async def get_scan(self, scan_id: str, include_results: bool = True) -> Dict[str, Any]:
        """Get scan details."""
        response = await self.client.get(
            f"/scans/{scan_id}",
            params={"include_results": include_results},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()
    
    async def create_scan(self, rule_id: str) -> Dict[str, Any]:
        """Execute a scan."""
        self.request_started.emit()
        try:
            response = await self.client.post(
                "/scans",
                json={"rule_id": rule_id},
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()
        finally:
            self.request_finished.emit()
    
    async def cancel_scan(self, scan_id: str) -> Dict[str, Any]:
        """Cancel a running scan."""
        response = await self.client.post(f"/scans/{scan_id}/cancel", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    # Device endpoints
    async def list_devices(
        self,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """List devices."""
        params = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        
        response = await self.client.get("/devices", params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    async def get_device(self, device_id: str) -> Dict[str, Any]:
        """Get device details."""
        response = await self.client.get(f"/devices/{device_id}", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    # LLM endpoints
    async def interpret_rule(self, natural_language: str) -> Dict[str, Any]:
        """Convert natural language to rule conditions."""
        response = await self.client.post(
            "/llm/interpret-rule",
            json={"natural_language": natural_language},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()


# Singleton instance
_api_client: Optional[ApiClient] = None


def get_api_client() -> ApiClient:
    """Get API client singleton."""
    global _api_client
    if _api_client is None:
        _api_client = ApiClient()
    return _api_client
```

---

## Step 4: Base ViewModel

📝 **PROMPT: Create MVVM base classes for PySide6**
```
Create base ViewModel class for PySide6 MVVM pattern:
- Property change notifications using Qt signals
- Async task management with QThread
- Loading state management
- Error handling
```

**File: `desktop-app/src/it_ops_agent/viewmodels/base.py`**

```python
"""Base ViewModel classes for MVVM pattern."""

import asyncio
from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, Signal, Property, Slot, QThread, QRunnable, QThreadPool


class AsyncWorker(QRunnable):
    """Worker for running async functions in thread pool."""
    
    def __init__(self, coro, callback: Optional[Callable] = None, error_callback: Optional[Callable] = None):
        super().__init__()
        self.coro = coro
        self.callback = callback
        self.error_callback = error_callback
    
    def run(self):
        """Execute the coroutine."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.coro)
            if self.callback:
                self.callback(result)
        except Exception as e:
            if self.error_callback:
                self.error_callback(e)
        finally:
            loop.close()


class BaseViewModel(QObject):
    """Base class for all ViewModels."""
    
    # Common signals
    loading_changed = Signal(bool)
    error_occurred = Signal(str)
    data_changed = Signal()
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._is_loading = False
        self._error: Optional[str] = None
        self._thread_pool = QThreadPool.globalInstance()
    
    @Property(bool, notify=loading_changed)
    def is_loading(self) -> bool:
        """Loading state property."""
        return self._is_loading
    
    @is_loading.setter
    def is_loading(self, value: bool):
        if self._is_loading != value:
            self._is_loading = value
            self.loading_changed.emit(value)
    
    @Property(str, notify=error_occurred)
    def error(self) -> Optional[str]:
        """Error message property."""
        return self._error
    
    @error.setter
    def error(self, value: Optional[str]):
        self._error = value
        if value:
            self.error_occurred.emit(value)
    
    def run_async(
        self,
        coro,
        callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None,
    ):
        """Run an async function in background thread."""
        self.is_loading = True
        
        def on_complete(result):
            self.is_loading = False
            if callback:
                callback(result)
        
        def on_error(e):
            self.is_loading = False
            self.error = str(e)
            if error_callback:
                error_callback(e)
        
        worker = AsyncWorker(coro, on_complete, on_error)
        self._thread_pool.start(worker)
    
    @Slot()
    def refresh(self):
        """Refresh data - override in subclasses."""
        pass
    
    def clear_error(self):
        """Clear current error."""
        self._error = None


class ListViewModel(BaseViewModel):
    """Base class for list-based ViewModels."""
    
    items_changed = Signal()
    pagination_changed = Signal()
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._items: list = []
        self._total: int = 0
        self._page: int = 1
        self._page_size: int = 20
        self._pages: int = 0
    
    @Property(list, notify=items_changed)
    def items(self) -> list:
        """Items list property."""
        return self._items
    
    @items.setter
    def items(self, value: list):
        self._items = value
        self.items_changed.emit()
    
    @Property(int, notify=pagination_changed)
    def total(self) -> int:
        return self._total
    
    @Property(int, notify=pagination_changed)
    def page(self) -> int:
        return self._page
    
    @page.setter
    def page(self, value: int):
        if self._page != value:
            self._page = value
            self.pagination_changed.emit()
            self.refresh()
    
    @Property(int, notify=pagination_changed)
    def pages(self) -> int:
        return self._pages
    
    @Slot()
    def next_page(self):
        """Go to next page."""
        if self._page < self._pages:
            self.page = self._page + 1
    
    @Slot()
    def prev_page(self):
        """Go to previous page."""
        if self._page > 1:
            self.page = self._page - 1
```

---

## Step 5: Dashboard ViewModel

**File: `desktop-app/src/it_ops_agent/viewmodels/dashboard_vm.py`**

```python
"""Dashboard ViewModel."""

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Property, Signal, Slot

from it_ops_agent.api.client import get_api_client
from it_ops_agent.viewmodels.base import BaseViewModel


class DashboardViewModel(BaseViewModel):
    """ViewModel for dashboard screen."""
    
    summary_changed = Signal()
    trends_changed = Signal()
    recent_scans_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._api = get_api_client()
        
        # Summary stats
        self._active_rules = 0
        self._scans_24h = 0
        self._total_issues = 0
        self._critical_issues = 0
        self._pending_actions = 0
        
        # Trends data
        self._trends: List[Dict[str, Any]] = []
        
        # Recent scans
        self._recent_scans: List[Dict[str, Any]] = []
    
    # Summary properties
    @Property(int, notify=summary_changed)
    def active_rules(self) -> int:
        return self._active_rules
    
    @Property(int, notify=summary_changed)
    def scans_24h(self) -> int:
        return self._scans_24h
    
    @Property(int, notify=summary_changed)
    def total_issues(self) -> int:
        return self._total_issues
    
    @Property(int, notify=summary_changed)
    def critical_issues(self) -> int:
        return self._critical_issues
    
    @Property(int, notify=summary_changed)
    def pending_actions(self) -> int:
        return self._pending_actions
    
    @Property(list, notify=trends_changed)
    def trends(self) -> List[Dict[str, Any]]:
        return self._trends
    
    @Property(list, notify=recent_scans_changed)
    def recent_scans(self) -> List[Dict[str, Any]]:
        return self._recent_scans
    
    @Slot()
    def refresh(self):
        """Refresh all dashboard data."""
        self.load_summary()
        self.load_trends()
        self.load_recent_scans()
    
    def load_summary(self):
        """Load dashboard summary."""
        async def fetch():
            return await self._api.get_dashboard_summary()
        
        def on_success(data):
            self._active_rules = data.get("active_rules", 0)
            self._scans_24h = data.get("scans_24h", 0)
            self._total_issues = data.get("total_issues_7d", 0)
            self._critical_issues = data.get("critical_issues_7d", 0)
            self._pending_actions = data.get("pending_actions", 0)
            self.summary_changed.emit()
        
        self.run_async(fetch(), on_success)
    
    def load_trends(self, days: int = 7):
        """Load severity trends."""
        async def fetch():
            return await self._api.get_severity_trends(days)
        
        def on_success(data):
            self._trends = data
            self.trends_changed.emit()
        
        self.run_async(fetch(), on_success)
    
    def load_recent_scans(self, limit: int = 10):
        """Load recent scans."""
        async def fetch():
            return await self._api.get_recent_scans(limit)
        
        def on_success(data):
            self._recent_scans = data
            self.recent_scans_changed.emit()
        
        self.run_async(fetch(), on_success)
```

---

## Step 6: Rules ViewModel

**File: `desktop-app/src/it_ops_agent/viewmodels/rules_vm.py`**

```python
"""Rules list ViewModel."""

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Property, Signal, Slot

from it_ops_agent.api.client import get_api_client
from it_ops_agent.viewmodels.base import ListViewModel


class RulesViewModel(ListViewModel):
    """ViewModel for rules list screen."""
    
    rule_selected = Signal(str)  # rule_id
    rule_created = Signal(str)   # rule_id
    rule_deleted = Signal(str)   # rule_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._api = get_api_client()
        
        # Filter state
        self._search: str = ""
        self._entity_type: Optional[str] = None
        
        # Selected rule
        self._selected_rule: Optional[Dict[str, Any]] = None
    
    @Property(str)
    def search(self) -> str:
        return self._search
    
    @search.setter
    def search(self, value: str):
        if self._search != value:
            self._search = value
            self._page = 1  # Reset to first page
            self.refresh()
    
    @Property(str)
    def entity_type(self) -> Optional[str]:
        return self._entity_type
    
    @entity_type.setter
    def entity_type(self, value: Optional[str]):
        if self._entity_type != value:
            self._entity_type = value
            self._page = 1
            self.refresh()
    
    @Property("QVariant")
    def selected_rule(self) -> Optional[Dict[str, Any]]:
        return self._selected_rule
    
    @Slot()
    def refresh(self):
        """Refresh rules list."""
        async def fetch():
            return await self._api.list_rules(
                search=self._search or None,
                entity_type=self._entity_type,
                page=self._page,
                page_size=self._page_size,
            )
        
        def on_success(data):
            self._items = data.get("items", [])
            self._total = data.get("total", 0)
            self._pages = data.get("pages", 0)
            self.items_changed.emit()
            self.pagination_changed.emit()
        
        self.run_async(fetch(), on_success)
    
    @Slot(str)
    def select_rule(self, rule_id: str):
        """Select a rule for viewing/editing."""
        async def fetch():
            return await self._api.get_rule(rule_id)
        
        def on_success(data):
            self._selected_rule = data
            self.rule_selected.emit(rule_id)
        
        self.run_async(fetch(), on_success)
    
    @Slot(str)
    def delete_rule(self, rule_id: str):
        """Delete a rule."""
        async def do_delete():
            await self._api.delete_rule(rule_id)
            return rule_id
        
        def on_success(deleted_id):
            self.rule_deleted.emit(deleted_id)
            self.refresh()
        
        self.run_async(do_delete(), on_success)
    
    @Slot(str)
    def clone_rule(self, rule_id: str):
        """Clone a rule."""
        async def do_clone():
            return await self._api.clone_rule(rule_id)
        
        def on_success(data):
            self.rule_created.emit(data["id"])
            self.refresh()
        
        self.run_async(do_clone(), on_success)
    
    @Slot(str)
    def run_scan(self, rule_id: str):
        """Execute a scan for a rule."""
        async def do_scan():
            return await self._api.create_scan(rule_id)
        
        def on_success(data):
            # Navigate to scan results or show notification
            pass
        
        self.run_async(do_scan(), on_success)
```

---

## Step 7: Main Window

📝 **PROMPT: Create PySide6 main window with navigation**
```
Create a main window for PySide6 application with:
- Sidebar navigation
- Header with user info and search
- Content area that switches between views
- Status bar with notifications
- Dark theme styling
```

**File: `desktop-app/src/it_ops_agent/views/main_window.py`**

```python
"""Main application window."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QStatusBar, QLabel,
)
from PySide6.QtCore import Qt, Slot

from it_ops_agent.config import get_config
from it_ops_agent.views.components.sidebar import Sidebar
from it_ops_agent.views.components.header import Header
from it_ops_agent.views.dashboard import DashboardView
from it_ops_agent.views.rules_list import RulesListView
from it_ops_agent.views.rule_builder import RuleBuilderView
from it_ops_agent.views.scan_results import ScanResultsView


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.config = get_config()
        
        self._setup_ui()
        self._setup_connections()
        self._apply_theme()
    
    def _setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("IT Operations AI Agent")
        self.resize(self.config.window_width, self.config.window_height)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.setFixedWidth(self.config.sidebar_width)
        main_layout.addWidget(self.sidebar)
        
        # Content area
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Header
        self.header = Header()
        content_layout.addWidget(self.header)
        
        # Stacked widget for views
        self.content_stack = QStackedWidget()
        content_layout.addWidget(self.content_stack, 1)
        
        main_layout.addLayout(content_layout, 1)
        
        # Create views
        self.dashboard_view = DashboardView()
        self.rules_view = RulesListView()
        self.rule_builder_view = RuleBuilderView()
        self.scan_results_view = ScanResultsView()
        
        # Add views to stack
        self.content_stack.addWidget(self.dashboard_view)  # Index 0
        self.content_stack.addWidget(self.rules_view)       # Index 1
        self.content_stack.addWidget(self.rule_builder_view) # Index 2
        self.content_stack.addWidget(self.scan_results_view) # Index 3
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
    
    def _setup_connections(self):
        """Set up signal connections."""
        # Sidebar navigation
        self.sidebar.navigation_changed.connect(self._on_navigation)
        
        # View-specific connections
        self.rules_view.create_rule_clicked.connect(self._show_rule_builder)
        self.rules_view.edit_rule_clicked.connect(self._edit_rule)
        self.rules_view.view_scan_clicked.connect(self._show_scan_results)
        
        self.rule_builder_view.rule_saved.connect(self._on_rule_saved)
        self.rule_builder_view.cancelled.connect(self._show_rules_list)
    
    def _apply_theme(self):
        """Apply theme stylesheet."""
        try:
            from importlib.resources import files
            style_file = files("it_ops_agent.resources.styles").joinpath("dark_theme.qss")
            style = style_file.read_text()
            self.setStyleSheet(style)
        except Exception:
            # Use default styling if resource not found
            pass
    
    @Slot(str)
    def _on_navigation(self, page: str):
        """Handle sidebar navigation."""
        page_map = {
            "dashboard": 0,
            "rules": 1,
            "scans": 3,
            "devices": 4,
            "applications": 5,
        }
        
        index = page_map.get(page, 0)
        self.content_stack.setCurrentIndex(index)
        
        # Refresh the view
        current_widget = self.content_stack.currentWidget()
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()
    
    @Slot()
    def _show_rule_builder(self):
        """Show rule builder for new rule."""
        self.rule_builder_view.set_rule(None)
        self.content_stack.setCurrentWidget(self.rule_builder_view)
    
    @Slot(str)
    def _edit_rule(self, rule_id: str):
        """Show rule builder for editing."""
        self.rule_builder_view.load_rule(rule_id)
        self.content_stack.setCurrentWidget(self.rule_builder_view)
    
    @Slot(str)
    def _show_scan_results(self, scan_id: str):
        """Show scan results view."""
        self.scan_results_view.load_scan(scan_id)
        self.content_stack.setCurrentWidget(self.scan_results_view)
    
    @Slot()
    def _on_rule_saved(self):
        """Handle rule saved."""
        self._show_rules_list()
        self.status_label.setText("Rule saved successfully")
    
    @Slot()
    def _show_rules_list(self):
        """Show rules list."""
        self.content_stack.setCurrentWidget(self.rules_view)
        self.rules_view.refresh()
```

---

## Step 8: Sidebar Component

**File: `desktop-app/src/it_ops_agent/views/components/sidebar.py`**

```python
"""Sidebar navigation component."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon


class NavButton(QPushButton):
    """Navigation button with icon."""
    
    def __init__(self, text: str, icon_name: str = None, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setObjectName("navButton")
        self.setCursor(Qt.PointingHandCursor)
        
        if icon_name:
            # Load icon from resources
            pass


class Sidebar(QWidget):
    """Sidebar navigation widget."""
    
    navigation_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        """Set up the sidebar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Logo/Title
        title = QLabel("IT Ops Agent")
        title.setObjectName("sidebarTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Navigation buttons
        self.nav_buttons = {}
        
        nav_items = [
            ("dashboard", "Dashboard", "dashboard"),
            ("rules", "Rules", "rules"),
            ("scans", "Scan History", "history"),
            ("devices", "Devices", "computer"),
            ("applications", "Applications", "apps"),
        ]
        
        for name, label, icon in nav_items:
            btn = NavButton(label, icon)
            btn.clicked.connect(lambda checked, n=name: self._on_nav_click(n))
            self.nav_buttons[name] = btn
            layout.addWidget(btn)
        
        # Spacer
        layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        
        # Settings button at bottom
        settings_btn = NavButton("Settings", "settings")
        settings_btn.clicked.connect(lambda: self._on_nav_click("settings"))
        self.nav_buttons["settings"] = settings_btn
        layout.addWidget(settings_btn)
        
        # Select dashboard by default
        self.nav_buttons["dashboard"].setChecked(True)
    
    def _setup_connections(self):
        """Set up signal connections."""
        pass
    
    def _on_nav_click(self, name: str):
        """Handle navigation button click."""
        # Uncheck other buttons
        for btn_name, btn in self.nav_buttons.items():
            btn.setChecked(btn_name == name)
        
        self.navigation_changed.emit(name)
```

---

## Step 9: Dashboard View

**File: `desktop-app/src/it_ops_agent/views/dashboard.py`**

```python
"""Dashboard view."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis

from it_ops_agent.viewmodels.dashboard_vm import DashboardViewModel


class StatCard(QFrame):
    """Card widget for displaying a statistic."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        
        layout = QVBoxLayout(self)
        
        self.title_label = QLabel(title)
        self.title_label.setObjectName("statTitle")
        layout.addWidget(self.title_label)
        
        self.value_label = QLabel("0")
        self.value_label.setObjectName("statValue")
        layout.addWidget(self.value_label)
    
    def set_value(self, value):
        """Set the displayed value."""
        self.value_label.setText(str(value))


class DashboardView(QWidget):
    """Dashboard screen widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardView")
        
        self._vm = DashboardViewModel()
        
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        """Set up the dashboard UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Page title
        title = QLabel("Dashboard")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        # Stats row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        self.active_rules_card = StatCard("Active Rules")
        self.scans_card = StatCard("Scans (24h)")
        self.issues_card = StatCard("Issues (7d)")
        self.critical_card = StatCard("Critical Issues")
        self.actions_card = StatCard("Pending Actions")
        
        stats_layout.addWidget(self.active_rules_card)
        stats_layout.addWidget(self.scans_card)
        stats_layout.addWidget(self.issues_card)
        stats_layout.addWidget(self.critical_card)
        stats_layout.addWidget(self.actions_card)
        
        layout.addLayout(stats_layout)
        
        # Charts and tables row
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        
        # Trends chart
        chart_container = QFrame()
        chart_container.setObjectName("chartContainer")
        chart_layout = QVBoxLayout(chart_container)
        
        chart_title = QLabel("Severity Trends")
        chart_title.setObjectName("sectionTitle")
        chart_layout.addWidget(chart_title)
        
        self.trends_chart = QChartView()
        self.trends_chart.setMinimumHeight(300)
        chart_layout.addWidget(self.trends_chart)
        
        content_layout.addWidget(chart_container, 2)
        
        # Recent scans table
        scans_container = QFrame()
        scans_container.setObjectName("tableContainer")
        scans_layout = QVBoxLayout(scans_container)
        
        scans_title = QLabel("Recent Scans")
        scans_title.setObjectName("sectionTitle")
        scans_layout.addWidget(scans_title)
        
        self.scans_table = QTableWidget()
        self.scans_table.setColumnCount(4)
        self.scans_table.setHorizontalHeaderLabels(["Rule", "Status", "Matches", "Time"])
        self.scans_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.scans_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.scans_table.setSelectionBehavior(QTableWidget.SelectRows)
        scans_layout.addWidget(self.scans_table)
        
        content_layout.addWidget(scans_container, 1)
        
        layout.addLayout(content_layout, 1)
    
    def _setup_connections(self):
        """Set up signal connections."""
        self._vm.summary_changed.connect(self._update_summary)
        self._vm.trends_changed.connect(self._update_trends_chart)
        self._vm.recent_scans_changed.connect(self._update_scans_table)
    
    @Slot()
    def refresh(self):
        """Refresh dashboard data."""
        self._vm.refresh()
    
    @Slot()
    def _update_summary(self):
        """Update summary statistics."""
        self.active_rules_card.set_value(self._vm.active_rules)
        self.scans_card.set_value(self._vm.scans_24h)
        self.issues_card.set_value(self._vm.total_issues)
        self.critical_card.set_value(self._vm.critical_issues)
        self.actions_card.set_value(self._vm.pending_actions)
    
    @Slot()
    def _update_trends_chart(self):
        """Update trends chart."""
        chart = QChart()
        chart.setTitle("")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Create series for each severity
        severities = {
            "critical": ("Critical", "#EF4444"),
            "high": ("High", "#F97316"),
            "medium": ("Medium", "#EAB308"),
            "low": ("Low", "#22C55E"),
        }
        
        for sev_key, (sev_name, color) in severities.items():
            series = QLineSeries()
            series.setName(sev_name)
            
            for point in self._vm.trends:
                # Add data points
                pass
            
            chart.addSeries(series)
        
        self.trends_chart.setChart(chart)
    
    @Slot()
    def _update_scans_table(self):
        """Update recent scans table."""
        self.scans_table.setRowCount(len(self._vm.recent_scans))
        
        for row, scan in enumerate(self._vm.recent_scans):
            self.scans_table.setItem(row, 0, QTableWidgetItem(scan.get("rule_name", "")))
            self.scans_table.setItem(row, 1, QTableWidgetItem(scan.get("status", "")))
            self.scans_table.setItem(row, 2, QTableWidgetItem(str(scan.get("total_matched", 0))))
            
            created = scan.get("created_at", "")
            if created:
                # Format datetime
                pass
            self.scans_table.setItem(row, 3, QTableWidgetItem(created))
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        self.refresh()
```

---

## Step 10: Dark Theme Stylesheet

**File: `desktop-app/src/it_ops_agent/resources/styles/dark_theme.qss`**

```css
/* Dark theme for IT Operations AI Agent */

/* Main window */
QMainWindow {
    background-color: #1a1a2e;
}

/* Sidebar */
#sidebar {
    background-color: #16213e;
    border-right: 1px solid #0f3460;
}

#sidebarTitle {
    font-size: 18px;
    font-weight: bold;
    color: #00d9ff;
    padding: 20px 10px;
}

#navButton {
    background-color: transparent;
    color: #a0a0a0;
    border: none;
    padding: 12px 20px;
    text-align: left;
    font-size: 14px;
}

#navButton:hover {
    background-color: #0f3460;
    color: #ffffff;
}

#navButton:checked {
    background-color: #0f3460;
    color: #00d9ff;
    border-left: 3px solid #00d9ff;
}

/* Header */
#header {
    background-color: #1a1a2e;
    border-bottom: 1px solid #0f3460;
    padding: 10px 20px;
}

/* Page title */
#pageTitle {
    font-size: 24px;
    font-weight: bold;
    color: #ffffff;
    margin-bottom: 10px;
}

/* Section title */
#sectionTitle {
    font-size: 16px;
    font-weight: bold;
    color: #ffffff;
    margin-bottom: 10px;
}

/* Stat cards */
#statCard {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 8px;
    padding: 16px;
    min-width: 150px;
}

#statTitle {
    font-size: 12px;
    color: #a0a0a0;
    margin-bottom: 8px;
}

#statValue {
    font-size: 28px;
    font-weight: bold;
    color: #ffffff;
}

/* Tables */
QTableWidget {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 4px;
    gridline-color: #0f3460;
}

QTableWidget::item {
    color: #ffffff;
    padding: 8px;
}

QTableWidget::item:selected {
    background-color: #0f3460;
}

QHeaderView::section {
    background-color: #1a1a2e;
    color: #a0a0a0;
    padding: 10px;
    border: none;
    border-bottom: 1px solid #0f3460;
    font-weight: bold;
}

/* Buttons */
QPushButton {
    background-color: #0f3460;
    color: #ffffff;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #1a4980;
}

QPushButton:pressed {
    background-color: #0a2540;
}

QPushButton#primaryButton {
    background-color: #00d9ff;
    color: #1a1a2e;
}

QPushButton#primaryButton:hover {
    background-color: #33e1ff;
}

QPushButton#dangerButton {
    background-color: #ef4444;
    color: #ffffff;
}

/* Input fields */
QLineEdit, QTextEdit, QComboBox {
    background-color: #16213e;
    color: #ffffff;
    border: 1px solid #0f3460;
    padding: 10px;
    border-radius: 4px;
}

QLineEdit:focus, QTextEdit:focus {
    border-color: #00d9ff;
}

/* Scrollbars */
QScrollBar:vertical {
    background-color: #16213e;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #0f3460;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #1a4980;
}

/* Status bar */
QStatusBar {
    background-color: #16213e;
    color: #a0a0a0;
    border-top: 1px solid #0f3460;
}
```

---

## Step 11: Main Entry Point

**File: `desktop-app/src/it_ops_agent/main.py`**

```python
"""Application entry point."""

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from it_ops_agent.views.main_window import MainWindow


def main():
    """Main entry point."""
    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("IT Operations AI Agent")
    app.setOrganizationName("YourCompany")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

---

## Verification

### Run the Application

```powershell
# Install dependencies
cd desktop-app
pip install -r requirements.txt

# Run the application
python -m it_ops_agent.main
```

### Test with Mock Backend

Create a mock API for testing:

```python
# test_mock_server.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/api/v1/dashboard/summary")
def dashboard():
    return {
        "active_rules": 15,
        "scans_24h": 42,
        "total_issues_7d": 156,
        "critical_issues_7d": 12,
        "pending_actions": 3,
    }

if __name__ == "__main__":
    uvicorn.run(app, port=8001)
```

---

## Common Issues

### Issue: Qt plugin not found

**Solution:** Set Qt plugin path:

```python
import os
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = "/path/to/qt/plugins"
```

### Issue: Async operations blocking UI

**Solution:** Ensure all async work uses QThreadPool (implemented in BaseViewModel)

### Issue: Memory leaks from Qt objects

**Solution:** Set parent objects properly and use deleteLater() for dynamic widgets

---

## Next Steps

→ [08_LLM_Service.md](08_LLM_Service.md) - Implement AI-powered features

---

**Checkpoint:** You should now have:
- [ ] Desktop application launching
- [ ] Sidebar navigation working
- [ ] Dashboard displaying mock data
- [ ] Dark theme applied
- [ ] ViewModels properly bound to views
- [ ] API client integrated
