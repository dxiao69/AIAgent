# Key Questions to Prepare For - Roadmap Presentation

## 🔴 Critical Questions (High Priority)

### 1. Development Investment
**Question:** "What's the development cost in FTEs/hours?"

**Prepared Answer:**
- Phase 1 (Q1 2026): 14 weeks, 2-3 full-time developers
- Total effort breakdown:
  - Week 1-2: Foundation (Project setup, Database, Auth)
  - Week 3-5: Core Backend (MECM connector, Rule engine, API)
  - Week 5-7: Desktop Application
  - Week 7-9: AI/LLM Features
  - Week 9-12: Integrations (ServiceNow, Tachyon, Action Worker)
  - Week 12-14: Deployment & Testing

**Supporting Data:** See [Implementation Guides](../implementationDetails/00_README.md)

---

### 2. ROI Validation
**Question:** "How did you calculate 80% reduction / 10x productivity?"

**Prepared Answer:**
- These are **target metrics** to be validated in Phase 1 pilot
- Based on industry benchmarks from Gartner/Forrester for AIOps implementations
- We will baseline current state in Week 1-2 and measure:
  - Time spent on manual compliance checks (before/after)
  - Incident resolution time (before/after)
  - Number of devices one operator can effectively manage

**Action Item:** Add "*Target metrics to be validated in Phase 1 pilot*" footnote to Slide 2

---

### 3. Opportunity Cost
**Question:** "What else could the team build instead? What are we NOT doing?"

**Prepared Answer:**
- Current IT ops team spends 60-70% time on routine tasks
- This project frees capacity for:
  - Strategic cloud migration projects
  - Security posture improvements
  - New business capability delivery
- Alternative: Continue manual processes, hire more staff (est. 2-3 additional FTEs @ $X/year)

---

### 4. AI Safety & Risk
**Question:** "What if AI takes wrong action on production systems?"

**Prepared Answer:**
- **Phase 1 (L1-L2):** All actions require human approval - AI suggests only
- **Risk-based approval tiers:**
  - Low risk (auto-execute with logging): Disk cleanup, service restart
  - Medium risk (notify after): Patch deployment in maintenance window
  - High risk (require approval): Config changes, mass actions, production changes
- **Guardrails:**
  - PII filtering before LLM calls
  - Rollback capability for all actions
  - Audit trail for compliance
  - Kill switch for autonomous features

---

## 🟡 Important Questions (Medium Priority)

### 5. Team Skills
**Question:** "Do we have the skills in-house to build this?"

**Prepared Answer:**
- **Required skills:** Python/FastAPI, PostgreSQL, PySide6/Qt, LLM integration
- **Current team assessment:** [Assess your team here]
- **Training plan:** 
  - LangChain/LLM development (1-2 weeks ramp-up)
  - PySide6 desktop development (if needed)
- **Risk mitigation:** Detailed implementation guides reduce learning curve

---

### 6. Maintenance Burden
**Question:** "What's the maintenance burden after go-live?"

**Prepared Answer:**
- Estimated 20-30% of initial development effort annually
- Includes:
  - LLM prompt tuning and updates
  - Integration updates (ServiceNow, MECM API changes)
  - Security patches and dependency updates
  - New rule/action additions
- Recommendation: Allocate 0.5-1 FTE for ongoing maintenance

---

### 7. Integration Dependencies
**Question:** "What access/licenses do we need?"

**Prepared Answer:**
| System | Requirement | Status |
|--------|-------------|--------|
| MECM | Read-only SQL access to database | [✓/Pending] |
| ServiceNow | API credentials, integration user | [✓/Pending] |
| Tachyon (1E) | X.509 certificates, API access | [✓/Pending] |
| Azure AD | App registration for OAuth | [✓/Pending] |
| LLM | Azure OpenAI or API key | [✓/Pending] |

**Action Item:** Validate all access before development starts

---

### 8. IT Ops Staff Impact
**Question:** "What happens to IT ops jobs?"

**Prepared Answer:**
- **This is augmentation, not replacement**
- Staff will shift from:
  - Manual compliance checking → Exception handling
  - Routine incident response → Strategic improvements
  - Report generation → Analysis and planning
- Expected outcome: Handle 3x workload without additional hiring
- Consider: Involve IT ops team in Phase 1 pilot for buy-in

---

## 🟢 Anticipated Questions (Lower Priority)

### 9. Why Build vs. Buy?
**Question:** "Why not use ServiceNow ITOM, Dynatrace, or other commercial AIOps?"

**Prepared Answer:**
- **Cost:** Enterprise AIOps solutions cost $X00K+/year
- **Customization:** Our specific MECM + ServiceNow + Tachyon stack
- **Data control:** LLM integration with PII filtering - data stays in-house
- **Integration depth:** Direct access to existing tools without middleware

---

### 10. Phase 1 Standalone Value
**Question:** "If we stop at Phase 1, do we still get value?"

**Prepared Answer:**
**Yes.** Phase 1 delivers:
- Natural language compliance rule creation
- Automated scanning against MECM
- Real-time device monitoring dashboard
- ServiceNow ticket auto-creation
- Estimated 30-40% improvement in compliance visibility

Each phase builds on previous but delivers independent value.

---

### 11. Success Criteria
**Question:** "How do we know Phase 1 is successful?"

**Prepared Answer:**
**Go/No-Go criteria for Phase 2:**
| Metric | Target | Measurement |
|--------|--------|-------------|
| Rule creation time | 50% reduction | Time study |
| Compliance scan coverage | 95% of devices | System metrics |
| User adoption | 80% of IT ops team | Usage analytics |
| System uptime | 99% | Monitoring |
| LLM accuracy | 85% correct suggestions | Ground truth testing |

---

### 12. Demo / POC
**Question:** "Can we see a demo?"

**Prepared Answer:**
- Week 7 checkpoint: Basic rule creation + MECM query demo
- Week 12 checkpoint: Full Phase 1 functionality demo
- Pilot deployment: IT department (500 devices) for 4-week validation

---

## 📋 Pre-Meeting Checklist

Before presenting, confirm:

- [ ] All integration access validated (MECM, ServiceNow, Tachyon, Azure AD)
- [ ] LLM API costs estimated for pilot scale
- [ ] IT ops team informed and supportive
- [ ] Development team capacity confirmed
- [ ] Baseline metrics identified for measuring success
- [ ] Pilot scope defined (which devices, which team)

---

## 📎 Supporting Materials

- [Implementation Guides](../implementationDetails/00_README.md) - Full technical details
- [Non-Coding Checklist](../implementationDetails/14_Non_Coding_Checklist.md) - Infrastructure & access requirements
- [Deployment Guide](../implementationDetails/13_Deployment.md) - Production deployment plan

---

*Last Updated: January 31, 2026*
