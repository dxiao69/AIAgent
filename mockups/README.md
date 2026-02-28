# IT Operations AI Agent - UI Mockups Guide

This folder contains HTML/CSS mockups demonstrating the user interface for the IT Operations AI Agent system. These are static mockups designed to visualize the system workflow before implementation.

## 📁 Mockup Files

| File | Description | Key Features |
|------|-------------|--------------|
| [01_login.html](01_login.html) | Login Page | Microsoft Azure OAuth integration |
| [02_dashboard.html](02_dashboard.html) | Main Dashboard | Stats overview, recent activity, quick actions |
| [03_rules.html](03_rules.html) | Rules Management | Rule templates, rule list, filters |
| [04_scan_results.html](04_scan_results.html) | Scan Results (Devices) | AI suggestions panel, device list, bulk actions |
| [04_scan_results_apps.html](04_scan_results_apps.html) | Scan Results (Applications) | App list, CVE tracking, App Owner grouping |
| [05_rule_builder.html](05_rule_builder.html) | Rule Builder (Classic) | Entity type selector, NL input, visual condition builder |
| [05_rule_builder_wizard.html](05_rule_builder_wizard.html) | Rule Builder (Wizard) | 4-step wizard with contextual help |
| [05_wizard_step1.html](05_wizard_step1.html) | Wizard Step 1: Define Rule | Name, category, entity type, schedule, templates |
| [05_wizard_step2.html](05_wizard_step2.html) | Wizard Step 2: Set Conditions | NL input, AI interpretation, manual builder |
| [05_wizard_step3.html](05_wizard_step3.html) | Wizard Step 3: Choose Actions | AI recommendations, action cards, parameters |
| [05_wizard_step4.html](05_wizard_step4.html) | Wizard Step 4: Test & Activate | Summary, test run, preview, activation options |
| [06_approvals.html](06_approvals.html) | Action Approvals | Pending actions, confirmation modals, approval workflow |
| [07_action_definitions.html](07_action_definitions.html) | Action Definitions | Action metadata, risk levels, parameters, test status |
| [08_action_test.html](08_action_test.html) | Action Testing | Sandbox testing, validation steps, dry-run execution |
| [09_settings.html](09_settings.html) | Settings | General, LLM config, integrations, notifications, security |
| [10_logs.html](10_logs.html) | Logs & Audit Trail | Audit trail, action logs, integration logs, error tracking |
| [css/styles.css](css/styles.css) | Stylesheet | Design system, UX components, accessibility |

## ✨ UX Features (New)

All pages now include the following UX improvements:

| Feature | Description | Keyboard Shortcut |
|---------|-------------|-------------------|
| **Breadcrumbs** | Navigation trail showing current location | - |
| **Collapsible Sidebar** | Toggle sidebar for more workspace | `Ctrl+B` |
| **Wizard Patterns** | Multi-step forms with progress indicators | - |
| **Empty States** | Helpful guidance when no data exists | - |
| **Confirmation Modals** | Safety prompts for destructive actions | `Escape` to close |
| **Contextual Help** | Dismissible info banners for new users | - |
| **Quick Actions** | Dashboard cards for common tasks | - |

## 🚀 How to View the Mockups

### Method 1: Direct File Open (Simplest)
1. Navigate to the `mockups` folder in Windows Explorer
2. Double-click any `.html` file to open it in your default browser
3. Click the navigation links to move between pages

### Method 2: Using VS Code Live Server
1. Install the **Live Server** extension in VS Code
2. Right-click on any HTML file
3. Select **"Open with Live Server"**
4. The mockup will open in your browser with live reload support

### Method 3: Using Python HTTP Server
```powershell
cd c:\Users\dxiao\Documents\AIAgent\mockups
python -m http.server 8080
```
Then open `http://localhost:8080/01_login.html` in your browser.

## 📱 Navigation Flow

The mockups demonstrate the following user workflow:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Login     │────▶│  Dashboard  │────▶│   Rules     │
│ (01_login)  │     │(02_dashboard│     │ (03_rules)  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │ Scan Results│◀────│ Rule Builder│
                    │(04_scan)    │     │ (05_builder)│
                    └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Approvals  │
                    │(06_approvals│
                    └─────────────┘
```

## 🖥️ Screen Descriptions

### 1. Login Page (`01_login.html`)
- **Purpose**: Secure authentication via Microsoft Azure OAuth
- **Key Elements**:
  - Company branding
  - "Sign in with Microsoft" button
  - OAuth flow information
  - Security notice

### 2. Dashboard (`02_dashboard.html`)
- **Purpose**: Quick overview of system status
- **Key Elements**:
  - Statistics cards (devices scanned, issues found, pending approvals)
  - Issues by category chart
  - Recent activity feed
  - Quick actions panel

### 3. Rules Management (`03_rules.html`)
- **Purpose**: View and manage detection rules
- **Key Elements**:
  - Pre-built rule templates
  - Rules list with status indicators
  - Search and filter options
  - Create new rule button

### 4. Scan Results (`04_scan_results.html`)
- **Purpose**: View devices flagged by rules with AI suggestions
- **Key Elements**:
  - **AI Suggestions Panel** - LLM-generated remediation recommendations
  - Device table with issue details
  - Bulk selection for actions
  - Confidence scores for AI suggestions

### 5. Rule Builder (`05_rule_builder.html`)
- **Purpose**: Create rules using natural language or visual builder
- **Key Elements**:
  - **Natural Language Input** - Describe rules in plain English
  - AI interpretation preview
  - Visual condition builder (dropdowns)
  - Action selection checkboxes
  - Scheduling options

### 6. Approvals (`06_approvals.html`)
- **Purpose**: Review and approve pending actions
- **Key Elements**:
  - Pending approval cards with details
  - Device preview list
  - Approve/Reject buttons
  - Approver comments field
  - Safety warnings

## 🎨 Design System

### Color Palette
| Color | Hex | Usage |
|-------|-----|-------|
| Primary Blue | `#2563EB` | Primary buttons, links, accents |
| Success Green | `#28A745` | Success states, approved items |
| Warning Yellow | `#FFC107` | Warnings, pending items |
| Danger Red | `#DC3545` | Errors, rejections, critical issues |
| Neutral Gray | `#6C757D` | Secondary text, borders |

### Key UI Components
- **Cards**: Container for grouped content
- **Stats Cards**: Numeric metrics with icons
- **AI Panel**: Purple-accented section for AI features
- **Approval Cards**: Orange-highlighted pending actions
- **Device Tables**: Sortable data grids with checkboxes
- **Status Badges**: Colored indicators for states

### Accessibility Features
- WCAG 2.1 AA compliant color contrast
- Focus indicators for keyboard navigation
- Clear visual hierarchy
- Screen reader compatible structure

## 🔗 Interactive Elements

While these are static mockups, clicking these elements will navigate between pages:

| Element | Location | Navigates To |
|---------|----------|--------------|
| Sidebar Nav Items | All pages | Respective pages |
| "Create New Rule" | Dashboard, Rules | Rule Builder |
| "View All Issues" | Dashboard | Scan Results |
| "Login" button | Login page | Dashboard |
| Device table rows | Scan Results | (Simulated detail view) |

## 💡 Key Concepts Demonstrated

### 1. AI-Assisted Operations
- Natural language rule creation
- Confidence scores on AI suggestions
- Grouped recommendations by action type

### 2. Safety-First Design
- Mandatory approval workflow
- Separation of requestor and approver
- Device preview before execution
- Expiration on pending actions

### 3. Integration Points
- MECM collection creation
- ServiceNow ticket generation
- 1E Tachyon real-time actions
- Flexera GraphQL vulnerability evidence and remediation status
- Email notifications

### 4. Role-Based Access
- Viewer (read-only)
- Operator (create rules, request actions)
- Approver (approve/reject actions)
- Administrator (full access)

## 🛠️ Customization

To modify the mockups:

1. **Colors**: Edit CSS variables in `css/styles.css`:
   ```css
   :root {
       --primary-color: #2563EB;
       --success-color: #28A745;
       /* ... */
   }
   ```

2. **Content**: Edit the HTML files directly to change text, labels, or sample data.

3. **Layout**: Modify the CSS grid and flexbox properties for structural changes.

## 📋 Implementation Notes

These mockups represent the target UI for the Python/PySide6 desktop application. Key implementation considerations:

1. **Framework**: PySide6 (Qt for Python)
2. **Architecture**: MVVM pattern
3. **Styling**: Qt Style Sheets (QSS) - similar to CSS
4. **Charts**: Use Qt Charts or integrate Plotly
5. **Tables**: QTableView with custom models

## 📞 Questions?

Refer to the main documentation:
- [01_Requirements_Document.md](../docs/01_Requirements_Document.md)
- [02_Design_Document.md](../docs/02_Design_Document.md)
- [03_Implementation_Plan.md](../docs/03_Implementation_Plan.md)
