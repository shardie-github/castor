# YC Team Notes

**For:** YC Application & Interview Prep  
**Last Updated:** 2024

---

## Team Information From Repo

### Founders / Team Members

> TODO: Founders to supply real data here

**Current Status:** No explicit team information found in repo (no AUTHORS file, no team.md, no package.json author fields with real names)

**Inferred from Codebase:**
- **Technical Execution:** Strong (comprehensive codebase, production-ready architecture)
- **Product Understanding:** Deep (detailed personas, user research, GTM strategy)
- **Domain Expertise:** Appears strong (podcast-specific features, industry knowledge)

---

## Role Split (Inferred)

### Technical Lead / CTO
**Evidence:**
- Comprehensive backend architecture (FastAPI, PostgreSQL, TimescaleDB, Redis)
- Multi-tenant architecture built from day one
- Production-ready infrastructure (monitoring, security, backups)
- Code quality (type hints, tests, documentation)

**Likely Responsibilities:**
- Backend architecture & development
- Database design & optimization
- Infrastructure & DevOps
- Technical strategy

---

### Product Lead / CEO
**Evidence:**
- Detailed user personas (`research/user-persona-matrix.md`)
- GTM strategy (`gtm/` directory)
- Pricing strategy (`monetization/pricing-plan.md`)
- MVP scope definition (`mvp/mvp-scope.md`)
- Competitive analysis (`strategy/competitive-moat.md`)

**Likely Responsibilities:**
- Product strategy & roadmap
- User research & validation
- GTM & distribution
- Business model & pricing

---

### Frontend Lead (If Separate Person)
**Evidence:**
- Next.js frontend with TypeScript
- Modern UI components (TailwindCSS, Headless UI)
- State management (Zustand, TanStack Query)
- Component architecture

**Likely Responsibilities:**
- Frontend development
- UI/UX design
- User experience optimization

---

## Founder Stories (Suggested by Repo)

### Story 1: "We Built This Because We Needed It"
**Evidence:** `README.md` - "We built this because we needed it. After running podcast operations at scale, we realized the tools don't exist."

**Suggested Narrative:**
- Founders ran podcast operations at scale
- Experienced pain points firsthand (manual reports, attribution chaos)
- Realized existing tools don't solve the problem
- Built solution to solve own problem

**YC Angle:** "Founder-market fit" - built by people who experienced the pain

---

### Story 2: "Technical Execution From Day One"
**Evidence:** 
- Production-ready architecture (multi-tenant, security, monitoring)
- Comprehensive codebase (200+ Python files, 70+ frontend files)
- Database migrations framework
- CI/CD pipelines

**Suggested Narrative:**
- Built for scale from day one (not MVP hack)
- Enterprise-grade architecture (multi-tenant, RBAC, audit logs)
- Production-ready infrastructure (monitoring, backups, disaster recovery)
- Technical depth (time-series DB, attribution models, AI framework)

**YC Angle:** "Technical execution" - can build and ship fast

---

### Story 3: "Deep Domain Expertise"
**Evidence:**
- Detailed user personas with Jobs-to-Be-Done framework
- Podcast-specific features (RSS ingestion, episode metadata, ad slots)
- Industry knowledge (sponsorship market, attribution models)
- Competitive analysis with podcast-specific competitors

**Suggested Narrative:**
- Deep understanding of podcast industry
- Know what podcasters need (not guessing)
- Understand sponsor/sponsor dynamics
- Built features that solve real problems

**YC Angle:** "Domain expertise" - know the market deeply

---

### Story 4: "Product-Market Fit Focus"
**Evidence:**
- User research framework (`validation/user-interview-framework.md`)
- Analytics events for validation (`validation/analytics-events.md`)
- Success metrics defined (`research/user-persona-matrix.md`)
- MVP scope focused on core value (`mvp/mvp-scope.md`)

**Suggested Narrative:**
- Focused on validation, not just building
- Defined success metrics upfront
- Built MVP focused on core value
- Ready to iterate based on user feedback

**YC Angle:** "Product-market fit focus" - know how to validate and iterate

---

## What Files/Docs Should Be Added

### 1. `/yc/TEAM.md` (New File)
**Should Include:**
- Founder names, backgrounds, roles
- Previous experience (companies, projects)
- Why this team for this problem
- Division of responsibilities
- Commitment level (full-time, part-time)
- Equity split (if applicable)

**Example Structure:**
```markdown
# Team

## Founders

### [Name] - CEO/Product
- Background: [Previous experience]
- Why this problem: [Story]
- Role: Product strategy, GTM, user research

### [Name] - CTO/Engineering
- Background: [Previous experience]
- Why this problem: [Story]
- Role: Backend architecture, infrastructure, technical strategy

## Advisors / Early Team
- [Name] - [Role] - [Background]
```

---

### 2. Update `README.md`
**Add Section:**
```markdown
## Team

[Brief team bios, why this team, what makes you unique]
```

---

### 3. Add `AUTHORS` File
**Include:**
- Founder names
- Contact information (optional)
- Roles/responsibilities

---

### 4. Add `package.json` Author Field (Frontend)
**Current:** No author field
**Should Include:**
- Author name(s)
- Contact information

---

## Guesses On Role Split (If Not Explicit)

### Scenario 1: Two Founders
- **Founder 1:** CEO/Product (product strategy, GTM, user research)
- **Founder 2:** CTO/Engineering (backend, infrastructure, technical strategy)
- **Frontend:** Either Founder 2 or contractor/early employee

### Scenario 2: Three Founders
- **Founder 1:** CEO/Product (product strategy, GTM)
- **Founder 2:** CTO/Backend (backend architecture, infrastructure)
- **Founder 3:** Frontend Lead (frontend development, UI/UX)

### Scenario 3: Solo Founder + Early Team
- **Founder:** CEO/Product/Engineering (full-stack, product strategy)
- **Early Team:** Frontend developer, designer (contractors or early employees)

---

## Evidence You Can Move Fast And Ship

### Technical Execution
- **Comprehensive Codebase:** 200+ Python files, 70+ frontend files
- **Production-Ready:** Monitoring, security, backups, disaster recovery
- **Architecture:** Multi-tenant, scalable, enterprise-grade from day one

### Product Execution
- **User Research:** Detailed personas, Jobs-to-Be-Done framework
- **GTM Strategy:** Comprehensive growth, SEO, content strategies
- **Pricing Strategy:** Detailed pricing tiers with conversion logic

### Speed Indicators
- **MVP Scope:** Clear, focused, achievable
- **Feature Completeness:** Core features implemented (ingestion, campaigns, attribution, reports)
- **Documentation:** Comprehensive docs (architecture, user research, GTM)

---

## What Good Content Would Look Like

### If You Have Team Background:
- Include founder bios with relevant experience
- Show previous projects/companies (if applicable)
- Explain why this team for this problem
- Include advisor/early team members (if applicable)
- Show commitment level (full-time, part-time)

### If You're Pre-Team:
- Show technical execution (codebase quality)
- Show product understanding (user research, GTM strategy)
- Show domain expertise (podcast-specific features)
- Explain why you're the right team (founder-market fit story)

---

## YC Interview Questions About Team

**Likely Questions:**
1. "Who's on the team?"
2. "What's your background?"
3. "Why this team for this problem?"
4. "How do you divide responsibilities?"
5. "What's your biggest weakness as a team?"
6. "Can you execute fast?"

**How to Answer (Using Repo Evidence):**
1. **Technical Execution:** Show codebase quality, architecture, production-readiness
2. **Product Understanding:** Show user research, personas, GTM strategy
3. **Domain Expertise:** Show podcast-specific features, industry knowledge
4. **Speed:** Show MVP completion, feature implementation, documentation

---

*This document should be updated with real team information before YC application/interview.*
