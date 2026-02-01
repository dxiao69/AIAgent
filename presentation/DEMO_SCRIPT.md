# ITOA Agent - Demo Script & Presentation Guide

## 📋 Pre-Presentation Checklist

### Technical Setup
- [ ] Open presentation in Chrome/Edge (fullscreen: press `F`)
- [ ] Test all mockup links work
- [ ] Have backup PDF version ready
- [ ] Ensure projector/screen share is working
- [ ] Close unnecessary applications

### Browser Tabs to Have Ready (in order)
1. `presentation/index.html` - Main presentation
2. `mockups/02_dashboard.html` - Dashboard demo
3. `mockups/05_wizard_step1.html` - Rule Builder Wizard
4. `mockups/04_scan_results.html` - Scan Results
5. `mockups/06_approvals.html` - Approvals page

---

## 🎬 Presentation Flow (20-25 minutes)

### Opening (Slide 1) - 1 minute

**Key Message:** "Today I'm introducing an AI-powered solution that will transform how we manage 100,000+ devices."

**Talking Points:**
- Highlight the 95% time savings
- Emphasize this is AI-powered, not just another tool
- Set expectation: "I'll show you a working prototype"

**READ THIS:**

> "Good morning everyone, thank you for joining me today."
>
> "I'm here to introduce something that I believe will change the way we do IT operations."
>
> "Right now, our team manages over 100,000 devices. Finding problems takes hours. Writing queries is complicated. And by the time we find issues, users are already complaining."
>
> "What if we could cut that time by 95 percent? What if instead of spending 2 to 4 hours searching for problematic devices, it took just 5 minutes?"
>
> "That's what this AI-powered solution does. And today, I'm going to show you a working prototype."

---

### The Challenge (Slide 2) - 2 minutes

**Key Message:** "These pain points are costing us hours every day."

**Talking Points:**
- Ask: "How long did your last MECM query take to write?"
- Reference specific team frustrations they've mentioned
- Show the contrast - left side is TODAY, right side is TOMORROW
- Engagement: Ask for raised hands

**READ THIS:**

> "Let me start by talking about what we deal with every day."
>
> "On the left side of this slide, you can see our current reality."
>
> "Writing MECM queries is hard. It requires specialized knowledge, and even experienced team members spend hours getting them right. Raise your hand if you've spent more than an hour this week just searching for devices with specific problems."
>
> *(Pause for hands)*
>
> "Finding devices is only half the battle. Once we find them, we have to manually check multiple systems - MECM for device info, ServiceNow for tickets, maybe Tachyon for real-time data. That's a lot of clicking and copying."
>
> "And here's the worst part - we're always reactive. Users call us with problems before we even know there's an issue."
>
> "Now look at the right side. This is what we're building. Plain English queries instead of complex syntax. All systems in one place. And the AI finds problems before users notice them."

---

### How It Works (Slide 3) - 2 minutes

**Key Message:** "Four simple steps: Define, Identify, Recommend, Execute"

**Talking Points:**
- Emphasize "plain English" - no SQL required
- Highlight the speed: "100K devices in under 5 minutes"
- Read the example query aloud
- Tie into upcoming demo

**READ THIS:**

> "So how does this actually work? Let me break it down into four simple steps."
>
> "Step one - Define. You type what you're looking for in plain English. No SQL. No WQL. Just describe what you need. For example: 'Find devices with less than 10 gigabytes of free disk space that haven't been patched in 30 days.'"
>
> "Step two - Identify. The AI translates your request into the right queries and scans all 100,000 devices. This takes about 5 minutes, not hours."
>
> "Step three - Recommend. Here's where it gets smart. The system doesn't just show you a list of devices. It analyzes the results and suggests what to do. Maybe it recommends running disk cleanup, or creating a ServiceNow ticket, or notifying app owners."
>
> "Step four - Execute. With one click, you can take action across multiple systems. Create a collection in MECM, open a ticket in ServiceNow, and send notifications - all at once."
>
> "In a moment, I'll show you exactly how this works in the demo."

---

### Key Capabilities (Slide 4) - 2 minutes

**Key Message:** "Six core capabilities that address our biggest challenges."

**Talking Points:**
- **Smart Rule Builder:** Type what you want, AI figures out the query
- **Dual Entity Support:** Devices AND applications with app owners
- **AI Recommendations:** Suggests solutions, not just finds problems
- **Approval Workflow:** Full audit trail - compliance approved
- **Multi-System Integration:** One action across MECM, ServiceNow, notifications
- **Ground Truth Testing:** AI quality assurance

**READ THIS:**

> "Let me highlight six key capabilities that make this solution powerful."
>
> "First, the Smart Rule Builder. You type what you want in plain English, and the AI figures out the technical query. No training required."
>
> "Second, we support both devices AND applications. You can search for problematic software just as easily as problematic hardware. And we track app owners too, so you know who to contact."
>
> "Third, AI-powered recommendations. The system doesn't just find problems - it suggests solutions based on best practices."
>
> "Fourth, a full approval workflow. Nothing happens automatically. Every action goes through review. This gives us a complete audit trail, which compliance loves."
>
> "Fifth, and this is important - multi-system integration. One action in our tool can create a MECM collection, open a ServiceNow ticket, AND notify the app owner. All automatically, from a single click."
>
> "Sixth, we built in Ground Truth Testing for AI quality. I'll explain this in the next slide."

---

### Business Impact (Slide 5) - 2 minutes

**Key Message:** "This isn't incremental improvement - it's transformation."

**Talking Points:**
- Point to specific numbers: "From 2-4 hours to 5 minutes"
- Emphasize proactive detection: "Finding problems BEFORE users complain"
- Calculate for them: "10+ hours per week saved per person"
- ROI: "500+ hours per year saved"

**READ THIS:**

> "Now let's talk about what this means for our team."
>
> "The numbers on this slide aren't guesses - they're based on how we work today."
>
> "Device identification time goes from 2 to 4 hours down to under 5 minutes. That's a 95 percent reduction."
>
> "Query creation goes from 30 to 60 minutes down to under 2 minutes. You just describe what you want."
>
> "But here's the number I'm most excited about - proactive issue detection. Right now, we're mostly reactive. With this system, we'll find 80 percent of problems before users even notice them."
>
> "Let me put this in perspective. If each team member saves just 10 hours per week - and I think that's conservative - that's 500 hours per year, per person. Multiply that by the team size, and we're talking about thousands of hours that can go toward strategic projects instead of manual searching."

---

### AI Quality Assurance (Slide 6) - 1.5 minutes

**Key Message:** "We've built in rigorous testing to ensure AI reliability."

**Talking Points:**
- Address the elephant in the room: "AI can make mistakes"
- Show confidence: "115+ test cases validate every AI component"
- Highlight accuracy targets: "90%+ accuracy required to deploy"
- Trust builder: Automatic testing blocks bad updates

**READ THIS:**

> "Now, I know what some of you might be thinking. AI can make mistakes. How do we trust it?"
>
> "That's exactly why we built Ground Truth Testing into the system."
>
> "We have over 115 test cases that validate every AI component. Before any update goes to production, these tests run automatically. If the AI accuracy drops below 90 percent, the update is blocked. It cannot ship."
>
> "This means we're not just hoping the AI works correctly - we're proving it works correctly, every single time we make a change."
>
> "And remember, the AI only makes recommendations. A human always reviews and approves before anything actually happens."

---

### Integration Architecture (Slide 7) - 1.5 minutes

**Key Message:** "This enhances your existing investments, it doesn't replace them."

**Talking Points:**
- Point to each integration: MECM, ServiceNow, Tachyon, LLM
- Emphasize: "We're not asking you to rip anything out"
- Note the LLM flexibility: "Can use OpenAI OR local QWEN for sensitive data"

**READ THIS:**

> "Let me quickly show you how this fits with our existing systems."
>
> "On the left, you see the data sources - MECM for device inventory, ServiceNow for tickets and changes, and Tachyon for real-time queries."
>
> "In the middle is our AI Agent - the brains of the operation. It uses a large language model to understand your requests and generate recommendations."
>
> "On the right, you see the actions we can take - creating collections, opening tickets, running scripts."
>
> "Here's what's important: we're not replacing anything. MECM stays. ServiceNow stays. Tachyon stays. This solution sits on top and makes them work together."
>
> "One more thing - for sensitive environments, we can run the AI locally using a model called QWEN. Nothing leaves our network if that's what you prefer."

---

### Implementation Timeline (Slide 8) - 2 minutes

**Key Message:** "14 weeks to production-ready with clear milestones."

**Talking Points:**
- Walk through each phase briefly (5 phases)
- Highlight: "5 demo milestones - you'll see progress every 2 weeks"
- Resource reality: "3.5 FTE - lean team, focused delivery"
- Call to action: "We can start as soon as we get the green light"

**READ THIS:**

> "So how long does this take to build? 14 weeks."
>
> "Let me walk you through the phases."
>
> "Phase 1, weeks 1 through 3 - we build the foundation. Database, basic API, core architecture."
>
> "Phase 2, weeks 4 through 6 - we add the AI components. Rule builder, scanning engine, recommendations."
>
> "Phase 3, weeks 7 through 9 - we build the desktop application. This is when you get something you can actually use."
>
> "Phase 4, weeks 10 through 12 - system integrations. Connect to MECM, ServiceNow, Tachyon."
>
> "Phase 5, weeks 13 through 14 - testing and deployment. Make sure everything works, then go live."
>
> "You won't have to wait until the end to see progress. We have 5 demo milestones planned - roughly every 2 weeks, you'll see working software."
>
> "The team needed is 3.5 full-time equivalents. That's 2 backend developers, 1 frontend developer, and shared DevOps support. It's a lean team with focused delivery."
>
> "We can start as soon as we get the green light."

---

## 🖥️ Live Demo Section (Slide 9) - 8-10 minutes

**Key Message:** "Let me show you this working prototype in action."

**Demo Path:**
1. Dashboard → 2. Rule Builder Wizard (4 steps) → 3. Scan Results → 4. Approvals

**TRANSITION - READ THIS:**

> "Okay, enough slides. Let me show you the actual prototype."
>
> "I'm going to walk you through four screens that demonstrate the core workflow."

---

### Demo 1: Dashboard (3 minutes)
**Open:** `mockups/02_dashboard.html`

**Highlights to Point Out:**
- Summary Cards (top): Device counts at a glance
- Fleet Health Chart: Visual breakdown with trends
- Recent Activity: Real-time logging
- Quick Actions (sidebar): One-click access

**READ THIS:**

> "This is the Dashboard - the first thing you see when you open the application."
>
> "Look at the top row of cards. At a glance, I can see we have 4,234 healthy devices, 847 devices with warnings, and 27 devices that need immediate action. I don't have to run a report or write a query - it's right there."
>
> "Below that is the Fleet Health chart. You can see the breakdown visually - healthy in green, warning in yellow, critical in red. Over time, you'll see trends. Are things getting better or worse?"
>
> "On the right side, there's Recent Activity. Every scan, every action, every approval - it's all logged here in real-time. You always know what's happening."
>
> "And notice the sidebar on the left. Quick Actions let you jump to common tasks with one click. New Rule, Run Scan, View Pending Actions."
>
> "The key point here is: the most important information is front and center. No digging. No multiple screens. Just open the app and you know the health of your entire fleet."

---

### Demo 2: Rule Builder Wizard (4 minutes)
**Open:** `mockups/05_wizard_step1.html`

**Highlights to Point Out:**
- Step 1: Basic info (name, entity type, systems)
- Step 2: Natural language → AI generates conditions
- Step 3: Configure actions (MECM, ServiceNow, email)
- Step 4: Review and save
- Key demo: Type plain English, watch AI generate query

**READ THIS:**

> "Now let me show you how to create a rule. This is where the AI really shines."
>
> "Step 1 is the Basic Information. I give the rule a name - let's say 'Low Disk Space Devices'. I choose the entity type - in this case, Devices. And I select which systems to scan - MECM, Tachyon, or both."
>
> "Simple form, nothing complicated yet."

**Click to Step 2 or open:** `mockups/05_wizard_step2.html`

> "Step 2 is where the magic happens. Look at this text box at the top. It says 'Describe what you're looking for in plain English.'"
>
> "I type: 'Find Windows 10 devices with less than 10 GB free disk space that haven't been patched in the last 30 days.'"
>
> "Watch what happens when I click Generate. The AI reads my request and creates the technical conditions automatically. Look - it added three conditions: Operating System contains Windows 10, Free Disk Space less than 10 GB, and Last Patch Date older than 30 days."
>
> "I didn't write any code. I didn't learn any query language. I just described what I wanted, and the AI figured it out."
>
> "If I want to adjust something, I can edit the conditions manually. Or I can type a new description and regenerate."

**Click to Step 3 or open:** `mockups/05_wizard_step3.html`

> "Step 3 is Actions. What should happen when we find matching devices?"
>
> "I can add multiple actions. For example: Create a MECM collection with these devices. Open a ServiceNow incident. Send an email to the IT team."
>
> "All of these will execute together when I approve the results. One click, multiple systems, all synchronized."

**Click to Step 4 or open:** `mockups/05_wizard_step4.html`

> "Step 4 is Review and Save. I see a summary of everything - the name, the conditions, the actions. If something looks wrong, I go back and fix it. If it looks good, I click Create Rule."
>
> "The whole process takes about 2 minutes. Compare that to the 30 to 60 minutes it takes to write a proper MECM query today."

---

### Demo 3: Scan Results (2 minutes)
**Open:** `mockups/04_scan_results.html`

**Highlights to Point Out:**
- Summary stats: Device count, scan duration
- Results table: Matching devices with details
- AI Insights panel: Pattern detection and suggestions
- Action buttons: Take action on results

**READ THIS:**

> "After a rule runs, you get the Scan Results page."
>
> "At the top, you see the summary. This scan found 156 devices matching our criteria. It ran in 4 minutes and 32 seconds. That's 100,000 devices scanned in under 5 minutes."
>
> "The main table shows every matching device - the name, the operating system, the specific values that triggered the match. In this case, you can see the free disk space for each device."
>
> "But here's the best part. Look at the right side panel - AI Insights."
>
> "The AI analyzed these 156 devices and noticed patterns. It says: '73% of these devices are in the Finance department.' It suggests: 'Consider scheduling disk cleanup during off-hours for minimal disruption.'"
>
> "The AI isn't just finding devices - it's helping you understand what you're looking at and what to do about it."
>
> "From here, I can select devices and take action, or I can let the automated actions we configured run with approval."

---

### Demo 4: Approvals (1 minute)
**Open:** `mockups/06_approvals.html`

**Highlights to Point Out:**
- Pending actions list: Nothing auto-executes
- Impact preview: See what will happen
- Approve/Reject workflow: Human control
- Audit trail: Full logging for compliance

**READ THIS:**

> "Finally, the Approvals page. This is our safety net."
>
> "Nothing executes automatically. Every recommended action shows up here first, waiting for human review."
>
> "You can see the pending actions in this list. Each one shows what will happen, how many devices are affected, and who requested it."
>
> "Click on any action to see the full details. Review the impact. If it looks good, click Approve. If something seems off, click Reject and add a comment."
>
> "Every approval, every rejection, every action taken - it's all logged with timestamps and user names. When compliance asks 'who did what and when,' we have the complete audit trail."
>
> "This is how we get the benefits of AI automation while keeping humans in control."

**Walk through each step:**

**Step 1 - Define Rule:**
> "First, we name our rule and choose what we're targeting - devices, applications, or both."

**Click Next → Step 2 (Set Conditions):**
> "Here's where it gets interesting. Watch this natural language box..."
> "I type: 'Devices with less than 10GB free disk space' - and the AI interprets it instantly."

**Highlight the AI interpretation panel:**
> "See how it converted my plain English into structured conditions? No SQL. No query builder. Just describe what you need."

**Click Next → Step 3 (Choose Actions):**
> "Based on the rule type, the AI RECOMMENDS what actions to take."
> "Notice the risk badges - High, Medium, Low. The system protects you from accidental damage."

**Click Next → Step 4 (Test & Activate):**
> "Before anything runs in production, you can do a dry run."
> "Look - it shows exactly which devices will be affected. No surprises."

---

### Demo 3: Scan Results (2 minutes)
**Open:** `mockups/04_scan_results.html`

**Script:**
> "After a rule executes, here's what you see."

**Highlight:**
1. **Summary bar**: "156 devices matched our criteria"
2. **Filtering options**: "Filter by any attribute instantly"
3. **Device details**: "Click any row for full details"
4. **Action button**: "Ready to take action? One click."

**Key Point:**
> "Notice the AI Insights panel on the right - it's already analyzing the results and suggesting next steps."

---

### Demo 4: Actions (1 minute)
**Open:** `mockups/06_approvals.html`

**Script:**
> "Finally, the action queue. Nothing executes without approval."

**Highlight:**
1. **Pending tab**: "Actions waiting for approval"
2. **Status indicators**: "Clear visual status"
3. **Approval workflow**: "Click to review details, then approve or reject"

**Compliance Point:**
> "Every action, every approval, every result - logged for audit. Compliance loves this."

---

## 📝 Closing (Slide 10) - 2 minutes

**Return to presentation**

**Key Message:** "We're ready to transform IT Operations."

**Talking Points:**
- Working prototype, not just a concept
- 14 weeks to production
- Scalable solution for 100K+ devices
- Team expertise on decisions, not data hunting
- Invitation for questions

**READ THIS:**

> "Let me wrap up with a few final thoughts."
>
> "What you've seen today is not a concept or a PowerPoint promise. It's a working prototype. The technology is proven. The architecture is solid. The timeline is realistic."
>
> "In 14 weeks, we can give every member of our team an AI-powered assistant. An assistant that finds problems before users complain. An assistant that suggests best-practice solutions. An assistant that executes across all our systems with full audit control."
>
> "We're managing over 100,000 devices today. That number will only grow. The way we work now - manual queries, multiple systems, reactive firefighting - it doesn't scale."
>
> "This solution does scale. And it puts our team's expertise where it matters most - making decisions, not hunting for data."
>
> "I'm excited about this. I think it can transform how we work. And I'd love to answer any questions you have."
>
> *(Pause)*
>
> "Questions?"

---

## ❓ Anticipated Questions & Answers

### Q: "What about data security/privacy with AI?"

**READ THIS:**

> "Great question. Security was a top priority when we designed this."
>
> "First, all personally identifiable information is filtered out before anything reaches the AI. Device names, user names - they're anonymized."
>
> "Second, we support running a local AI model called QWEN. If you prefer that nothing leaves our network, we can do that. The cloud AI is optional, not required."
>
> "Third, all communication is encrypted, and we follow the same security standards as our other enterprise tools."

---

### Q: "What if the AI makes mistakes?"

**READ THIS:**

> "That's a fair concern, and we've built in multiple safeguards."
>
> "First, we have Ground Truth Testing - over 115 test cases that run automatically before any update. If accuracy drops below 90 percent, the update is blocked."
>
> "Second, nothing executes without human approval. The AI makes recommendations. Humans decide whether to act on them."
>
> "Third, you can always see and edit what the AI generated. If a query doesn't look right, you adjust it before running."
>
> "So yes, AI can make mistakes. But with testing, approval workflows, and human oversight, we catch those mistakes before they cause problems."

---

### Q: "How long until we see value?"

**READ THIS:**

> "You won't have to wait 14 weeks to see results."
>
> "By week 5, you'll have a working rule builder and scanning engine. You can start creating rules and finding devices."
>
> "By week 7, you'll have the desktop application. That's a real tool your team can use."
>
> "By week 10, we'll have the integrations - MECM, ServiceNow, actions working end to end."
>
> "We've planned 5 demo milestones throughout the project. Every 2 to 3 weeks, you'll see working software and provide feedback."

---

### Q: "What resources do you need?"

**READ THIS:**

> "The team is 3.5 full-time equivalents for 14 weeks."
>
> "That breaks down to: 2 backend developers to build the API and AI components, 1 frontend developer for the desktop application, and part-time DevOps and QA support."
>
> "Infrastructure uses our existing OpenShift environment, so no new hardware needed."

---

### Q: "What about training?"

**READ THIS:**

> "One of the big advantages of natural language is that training is minimal."
>
> "If you can describe what you're looking for, you can use the system. There's no query language to learn."
>
> "We'll provide documentation and a short training session when we roll out. But honestly, most people will be productive within the first hour of using it."

---

### Q: "Can this integrate with [other system]?"

**READ THIS:**

> "The architecture is designed to be extensible. We use a connector-based approach."
>
> "We're starting with MECM, ServiceNow, and Tachyon because those are our core systems. But adding new connectors is straightforward."
>
> "If there's a specific system you're thinking about, let me know. We can evaluate it and potentially include it in the roadmap."

---

### Q: "What's the cost?"

**READ THIS:**

> "The primary cost is developer time - 3.5 FTE for 14 weeks."
>
> "Infrastructure cost is minimal because we use existing OpenShift."
>
> "For the AI, if we use OpenAI's cloud service, we estimate 50 to 100 dollars per month based on our expected usage. If we use the local QWEN model, that cost is zero."
>
> "Compared to the hours we'll save, the ROI is very favorable."

---

## 🎯 Key Messages to Reinforce

1. **Time Savings:** "95% reduction in identification time"
2. **AI-Powered:** "Natural language, not SQL"
3. **Safe:** "Approval workflow, audit trail, AI testing"
4. **Integrated:** "MECM + ServiceNow + Tachyon in one place"
5. **Achievable:** "14 weeks to production"

---

## 📁 Files Reference

| File | Purpose |
|------|---------|
| `presentation/index.html` | Main slide deck |
| `mockups/02_dashboard.html` | Dashboard demo |
| `mockups/03_rules.html` | Rules list view |
| `mockups/05_rule_builder.html` | Visual rule builder |
| `mockups/04_scan_results.html` | Scan results view |
| `mockups/05_wizard_step1.html` | Wizard Step 1 |
| `mockups/05_wizard_step2.html` | Wizard Step 2 |
| `mockups/05_wizard_step3.html` | Wizard Step 3 |
| `mockups/05_wizard_step4.html` | Wizard Step 4 |
| `mockups/06_approvals.html` | Actions/Approvals queue |
| `mockups/07_action_definitions.html` | Action definitions |
| `mockups/08_action_test.html` | Action testing |
| `mockups/09_settings.html` | Settings page |
| `mockups/10_logs.html` | Audit logs |
| `docs/Executive_Summary.md` | Leave-behind document |

---

## ⌨️ Presentation Controls

| Key | Action |
|-----|--------|
| `→` or `Space` | Next slide |
| `←` | Previous slide |
| `F` | Toggle fullscreen |
| Swipe | Touch navigation |

---

**Good luck with your presentation! 🚀**
