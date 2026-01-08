# Test Scenario 011: Startup Pivot - Strategic Debates

## Overview

A startup team (5 people) debates whether to pivot their failing product. This scenario tests:
- **Multiple strategy sessions** over weeks
- **Deep disagreements** on direction
- **Data-driven arguments** vs intuition
- **Changing positions** based on new information
- **Coalition forming** and persuasion

## Complexity: Complex (5 users) with HIGH discussion density

## Key Testing Focus
- Agent tracks evolving positions over time
- Agent recalls "who said what when"
- Agent can summarize arguments for/against
- Agent handles emotional and analytical content
- Agent tracks vote changes

## Prerequisites

- Docker containers running
- Backend running on http://localhost:8080
- Clean database

## Users

| Name   | Email            | Password | Role   |
|--------|-----------------|----------|--------|
| Vlad   | vlad@test.com   | test123  | owner  |
| Kirill | kirill@test.com | test123  | member |
| Anya   | anya@test.com   | test123  | member |
| Sergey | sergey@test.com | test123  | member |
| Mila   | mila@test.com   | test123  | member |

## Project

| Field       | Value                          |
|-------------|--------------------------------|
| Name        | SnapTask Pivot Decision        |

## Onboarding

```
Description: "Startup team deciding whether to pivot our failing product. Need to track arguments, positions, and decisions."
Answers: "1. Strategy discussions, argument tracking, position changes, voting. 2. CEO Vlad, CTO Kirill, Product Anya, Sales Sergey, Marketing Mila. 3. Make the right strategic decision for the company."
Confirm: "Yes, save it."
```

## Test Execution

### Phase 1: Setup

#### Step 1.1: Register and create project
```
POST /api/auth/register for all 5 users

User: Vlad
POST /api/projects { "name": "SnapTask Pivot Decision", "description": "Should we pivot or persevere?" }
Add all members
```

---

### Phase 2: Setting the Stage (Week 1)

#### Step 2.1: Current situation
```
User: Vlad
Chat: "Team, we need to have a serious discussion. SnapTask current status:
- Product: Task management app for freelancers
- Launched: 6 months ago
- Users: 2,300 registered, 180 active monthly
- Revenue: $890/month (45 paying users)
- Runway: 8 months at current burn rate
- Growth: -5% month over month

We're not hitting product-market fit. We need to decide: pivot or persevere?

Meeting scheduled for Friday to discuss options."
Expected: Agent saves current state
```

#### Step 2.2: Kirill's technical perspective
```
User: Kirill
Chat: "Before Friday, my technical assessment:
Our tech is solid. The app works well. The problem isn't engineering.

Looking at analytics:
- Users who stay past day 7 have 60% retention
- But 70% drop off in first 3 days
- Core feature (task boards) has low engagement
- Notification feature has surprisingly high engagement

Hypothesis: People don't want another task app. But they DO want something from us - just not sure what."
Expected: Agent saves technical analysis
```

#### Step 2.3: Sergey's sales perspective
```
User: Sergey
Chat: "Sales reality check:
- I've done 200+ calls with freelancers
- Most say 'nice app' but don't pay
- Common objection: 'I already use Notion/Trello/Todoist'
- BUT: 8 enterprise leads are interested in team version
- They'd pay $500-2000/month but need features we don't have

My take: We're in the wrong market segment. Enterprise, not freelancer."
Expected: Agent saves sales perspective
```

#### Step 2.4: Anya's product view
```
User: Anya
Chat: "Product analysis for discussion:
What freelancers actually said they need:
1. Client management (invoicing, contracts)
2. Time tracking (for billing)
3. Payment collection
4. Project task management (what we built)

We built #4, but #1-3 are bigger pain points. We have task management in a sea of task managers.

I think we should pivot to client management platform, not just tasks."
Expected: Agent saves product analysis
```

#### Step 2.5: Mila's market view
```
User: Mila
Chat: "Marketing perspective:
- CAC (customer acquisition cost): $45 per user
- Freelancer segment is oversaturated with free tools
- Enterprise segment: less competition but needs more features
- 'Client management for freelancers' has search volume but few good solutions

I'm torn. Both freelancer pivot (client mgmt) and enterprise pivot have merit."
Expected: Agent saves marketing view
```

---

### Phase 3: First Strategy Meeting (Week 1)

#### Step 3.1: Meeting begins
```
User: Vlad
Chat: "Friday strategy meeting starting. Based on everyone's input, I see 3 options:
A) Stay course - keep improving task management for freelancers
B) Pivot #1 - Client management platform for freelancers
C) Pivot #2 - Team task management for enterprises

Let's discuss each. Starting positions?"
Expected: Agent records options
```

#### Step 3.2: Initial positions
```
User: Sergey
Chat: "I'm strongly for Option C (enterprise). The money is there. I have warm leads. Freelancers don't pay."
Expected: Agent records position: Sergey = C
```

```
User: Anya
Chat: "Option B (client management). We understand freelancers, just built wrong product. Pivoting to enterprise means new market, new sales cycle, new everything."
Expected: Agent records position: Anya = B
```

```
User: Kirill
Chat: "Honestly, Option A with improvements. We're 6 months in - pivoting means throwing away work. Our retention for engaged users is good. We need better onboarding, not new product."
Expected: Agent records position: Kirill = A
```

```
User: Mila
Chat: "I'm between B and C. Leaning B because our brand and audience is freelancer-focused. Enterprise pivot = start from zero on marketing."
Expected: Agent records position: Mila = B (leaning)
```

```
User: Vlad
Chat: "I'm genuinely undecided. Save current positions:
- Sergey: C (enterprise)
- Anya: B (client mgmt)
- Kirill: A (stay course)
- Mila: B (leaning)
- Vlad: undecided"
Expected: Agent saves vote tally
```

#### Step 3.3: Debate on Option A
```
User: Sergey
Chat: "Kirill, with respect, Option A is denial. We've been 'improving' for 6 months. Growth is NEGATIVE. How much more time do we need?"
Expected: Agent logs argument against A
```

```
User: Kirill
Chat: "6 months isn't enough for product-market fit. Slack took 2 years. Our engaged users love us - that's signal. We're just not reaching enough of them."
Expected: Agent logs counter-argument for A
```

```
User: Anya
Chat: "Kirill, 180 MAU after 6 months isn't 'slow growth', it's no growth. The engaged users might love us but they're not enough to build a business on."
Expected: Agent logs Anya supporting Sergey's point
```

```
User: Kirill
Chat: "Fine, but what's our retention going to look like with a completely new product? We'll be back at zero. At least now we have SOMETHING working."
Expected: Agent logs concern
```

#### Step 3.4: Debate on Option B vs C
```
User: Vlad
Chat: "Let's compare B and C directly. Sergey, why enterprise over client management?"
Expected: Agent prompts debate
```

```
User: Sergey
Chat: "Revenue per customer. Freelancers pay $10-20/month IF they pay. Enterprises pay $500-2000. We need 50 enterprise clients to hit $50k MRR vs 2,500 freelancers. The math is clear."
Expected: Agent logs revenue argument
```

```
User: Anya
Chat: "But sales cycle! Enterprise deals take 3-6 months. We have 8 months runway. We'd close maybe 2-3 deals before running out of money. Freelancers can convert in days."
Expected: Agent logs counter-argument
```

```
User: Sergey
Chat: "I already have 8 warm leads. If even 3 close at $1000/month, that's $36k ARR and proves the model for fundraising."
Expected: Agent logs Sergey's response
```

```
User: Mila
Chat: "What would the enterprise product even look like? We'd need team features, admin panels, SSO, integrations... Kirill, how long to build that?"
Expected: Agent logs resource question
```

```
User: Kirill
Chat: "Minimum 4-5 months for enterprise-ready. We'd burn most runway building before selling. Option B (client mgmt) could ship in 8 weeks - most of our base is there."
Expected: Agent logs technical timeline
```

#### Step 3.5: First meeting conclusion
```
User: Vlad
Chat: "We're not ready to decide. Let's:
1. Sergey: Deeper qualification of enterprise leads this week
2. Anya: Mock up client management MVP scope
3. Kirill: Estimate build time for both options
4. Mila: Research competitors in both spaces

Next meeting: Wednesday. No decision today.

Current sentiment (not vote):
- Option A (stay): Kirill only
- Option B (client mgmt): Anya, Mila, maybe Vlad
- Option C (enterprise): Sergey

Save this meeting summary."
Expected: Agent saves meeting summary
```

---

### Phase 4: Week 2 Research

#### Step 4.1: Sergey's lead update
```
User: Sergey
Chat: "Enterprise lead deep-dive results:
8 leads → 5 serious after qualification

Lead 1: Marketing agency, 15 people, budget $800/month - needs integrations we don't have
Lead 2: Design studio, 8 people, budget $400/month - very interested, could close in 4 weeks
Lead 3: Software consultancy, 30 people, budget $1500/month - requires SSO (enterprise)
Lead 4: Creative agency, 12 people, budget $600/month - interested but comparing to Monday.com
Lead 5: Accounting firm, 20 people, budget $1000/month - needs audit logs, compliance features

Honest assessment: Only Lead 2 is closeable with current product. Others need 3-4 months dev work.

This changes my view somewhat. B might be faster to revenue than C."
Expected: Agent records Sergey's position softening
```

#### Step 4.2: Anya's MVP scope
```
User: Anya
Chat: "Client Management MVP scope (Option B):

Core features (8 weeks build):
- Client profiles and contact management
- Project/task linking to clients
- Simple invoicing (generate PDF)
- Time tracking per client/project
- Payment status tracking
- Basic contracts (templates)

Nice to have (later):
- Payment processing integration
- Client portal
- Automated reminders

This leverages 60% of existing code. We rebrand features, add client layer on top."
Expected: Agent saves MVP scope
```

#### Step 4.3: Kirill's technical estimate
```
User: Kirill
Chat: "Build estimates:

Option B (Client Management):
- MVP: 8 weeks
- Risk: Low (we know the stack)
- Can ship incrementally
- Most architecture reusable

Option C (Enterprise):
- MVP: 16-20 weeks
- Risk: High (new requirements)
- Need team features, permissions, SSO, audit logs
- Major architecture changes

I'm changing my position. Option A isn't working and C is too slow. I support Option B now."
Expected: Agent records Kirill changing from A to B
```

#### Step 4.4: Mila's competitive analysis
```
User: Mila
Chat: "Competitive landscape:

Option B (Client Management for Freelancers):
- HoneyBook: $5M+ funding, strong in creative industry
- Dubsado: Popular, but complex and expensive
- AND CO (now Fiverr): Shutting down features
- Gap: Simple, affordable solution. Market opening.

Option C (Enterprise Task Management):
- Monday.com: $1B+ company
- Asana: Public company
- ClickUp: $4B valuation
- Gap: None. Suicide mission competing with these.

My strong recommendation: Option B. Clear market opportunity. Option C is competing with giants."
Expected: Agent records competitive analysis
```

#### Step 4.5: Position update
```
User: Vlad
Chat: "Interesting week. Update on where everyone stands?
- Kirill changed from A to B
- Sergey is softening on C
- Mila and Anya were B
What's current state?"
Expected: Agent should recall and compare positions
```

---

### Phase 5: Second Strategy Meeting (Week 2)

#### Step 5.1: Sergey's internal conflict
```
User: Sergey
Chat: "I've been thinking all weekend. My heart says enterprise because that's where the BIG money is. But my head agrees with the data - we can't build enterprise features fast enough.

Still... I feel like we're giving up on a bigger opportunity. Freelancer market is crowded too. We'd be competing with HoneyBook."
Expected: Agent records Sergey's conflicted state
```

```
User: Anya
Chat: "Sergey, HoneyBook focuses on events and creative pros. We can focus on consultants, developers, designers - different positioning. And we can be simpler and cheaper."
Expected: Agent logs counter
```

```
User: Sergey
Chat: "Who are our best current users? The 45 paying ones?"
Expected: Agent prompts data request
```

```
User: Kirill
Chat: "Good question. Let me check... Our 45 paying users:
- 18 are freelance developers
- 12 are designers/creatives
- 8 are consultants
- 7 are other

None are teams/enterprises. Our paid users ARE freelancers. We just built wrong product for them."
Expected: Agent records user data
```

#### Step 5.2: The pivot emerges
```
User: Mila
Chat: "This is actually great news! We have 45 paying freelancers despite building the wrong product. Imagine if we build the RIGHT product for them.

I'm very confident now: Option B. Let's become 'the anti-HoneyBook' - simple client management for technical freelancers."
Expected: Agent records Mila's strong position
```

```
User: Sergey
Chat: "Okay, I'm convinced. I change my vote to B. But with conditions:
1. We add basic team features within 6 months (agencies grow from freelancers)
2. Pricing has tiers up to $50/month (not just $10)
3. I get to keep nurturing enterprise leads as long-term pipeline

Can we agree to these?"
Expected: Agent records Sergey's conditional switch to B
```

```
User: Vlad
Chat: "Sergey's conditions are reasonable. Anya, Kirill, Mila - thoughts?"
Expected: Agent prompts team response
```

```
User: Anya
Chat: "Condition 1: Yes, makes sense for growth path
Condition 2: Absolutely, value-based tiers
Condition 3: Sure, enterprise is future expansion

I agree with all."
Expected: Agent records agreement
```

```
User: Kirill
Chat: "Agreed on all. Team features after MVP is smart sequencing."
Expected: Agent records agreement
```

```
User: Mila
Chat: "Agreed. I actually love positioning this as 'grow with us' - start as freelancer, graduate to agency."
Expected: Agent records agreement
```

#### Step 5.3: Almost consensus
```
User: Vlad
Chat: "Are we ready to vote? It feels like we're all converging on Option B."
Expected: Agent prompts for formal vote
```

```
User: Kirill
Chat: "Before we vote, I want to acknowledge something. A week ago I was arguing for Option A. The data from Sergey's calls and Mila's competitive analysis changed my mind. That's how it should work - data over ego."
Expected: Agent records Kirill's reflection
```

```
User: Vlad
Chat: "Appreciated, Kirill. Final vote:
Option B (Client Management Pivot) - all in favor?"
Expected: Agent prompts votes
```

```
User: Sergey
Chat: "B - with the conditions we discussed"
```

```
User: Anya
Chat: "B"
```

```
User: Kirill
Chat: "B"
```

```
User: Mila
Chat: "B"
```

```
User: Vlad
Chat: "B from me too. UNANIMOUS.

Save this: On [today's date], the SnapTask team unanimously voted to pivot from task management to client management platform for freelancers.

Conditions agreed:
1. Team features in 6 month roadmap
2. Tiered pricing up to $50/month
3. Continue nurturing enterprise pipeline"
Expected: Agent saves unanimous decision
```

---

### Phase 6: Post-Decision Details (Week 3)

#### Step 6.1: New product name debate
```
User: Mila
Chat: "We need a new name. 'SnapTask' doesn't fit client management. Ideas:
- ClientFlow
- FreelanceHub
- Cliently
- Workfolio
- IndieOS

Thoughts?"
Expected: Agent saves naming options
```

```
User: Anya
Chat: "I like Workfolio - sounds professional, 'portfolio' vibe for freelancers."
Expected: Agent records preference
```

```
User: Sergey
Chat: "ClientFlow sounds too generic. Workfolio is interesting. What about 'Indie' something? IndieDesk? IndieHQ?"
Expected: Agent records feedback
```

```
User: Kirill
Chat: "IndieHQ is taken. IndieOS is interesting - implies it's the 'operating system' for your freelance business."
Expected: Agent records feedback
```

```
User: Mila
Chat: "IndieOS is cool but might confuse with actual OS software. I vote Workfolio. Clean, clear, professional."
Expected: Agent records preference
```

#### Step 6.2: More name debate
```
User: Vlad
Chat: "Current standings on names?"
Expected: Agent tallies:
- Workfolio: Anya, Mila
- IndieOS: Kirill likes it
- Others: mixed
```

```
User: Sergey
Chat: "New idea: ClientForge. Has 'forge' energy - you're building something."
Expected: Agent records new option
```

```
User: Anya
Chat: "ClientForge sounds too aggressive/masculine. We want freelancers of all types."
Expected: Agent records objection
```

```
User: Kirill
Chat: "What about Solo? As in 'solo professional'. SoloPro? SoloDesk?"
Expected: Agent records new ideas
```

```
User: Vlad
Chat: "Lots of options. Let's narrow down. Everyone pick top 2:
Mine: Workfolio, IndieOS"
Expected: Agent records preference
```

```
User: Sergey
Chat: "Workfolio, ClientForge"
```

```
User: Anya
Chat: "Workfolio, SoloDesk"
```

```
User: Kirill
Chat: "IndieOS, Workfolio"
```

```
User: Mila
Chat: "Workfolio, SoloDesk"
```

```
User: Vlad
Chat: "Workfolio appears in everyone's top 2! Decision made: We are now Workfolio.

Save: New brand name decided: Workfolio (unanimous second choice convergence)"
Expected: Agent saves brand decision
```

---

### Phase 7: Revisiting Decision (Week 5)

#### Step 7.1: Cold feet
```
User: Sergey
Chat: "Team, I'm having second thoughts. I was reviewing our pivot decision. In the 2 weeks since we decided:
- Enterprise Lead 2 went cold (chose Monday.com)
- 3 freelancers signed up but no conversions yet
- I'm worried we made the wrong call

Are we sure about this pivot? Did we give enterprise a fair chance?"
Expected: Agent records Sergey's doubt
```

```
User: Vlad
Chat: "Sergey, let's discuss. But remember - we had a thorough process. What specifically changed?"
Expected: Agent prompts discussion
```

```
User: Sergey
Chat: "Lead 2 was my strongest case for 'enterprise can close fast'. They chose a competitor. Maybe I oversold our chances."
Expected: Agent logs admission
```

#### Step 7.2: Team response
```
User: Anya
Chat: "Sergey, one lost deal doesn't invalidate the decision. We said enterprise takes 3-6 months - that lead proving it takes less was always a longshot."
Expected: Agent logs support for staying course
```

```
User: Kirill
Chat: "We're 2 weeks into MVP. I've rebuilt the data model around clients, invoicing is 50% done. Changing direction now means throwing away 2 weeks of work."
Expected: Agent logs sunk cost argument
```

```
User: Mila
Chat: "Sergey, I understand the fear. But remember our competitive analysis - enterprise means competing with Monday.com (the company that just stole your lead). Freelancer market is more open."
Expected: Agent logs market argument
```

#### Step 7.3: Vlad's leadership moment
```
User: Vlad
Chat: "Team, let's acknowledge Sergey's concerns are valid. Cold feet after big decisions is normal.

But let's review why we decided B:
1. Faster to market (8 weeks vs 16-20)
2. Less competitive pressure than enterprise
3. Our paying users ARE freelancers
4. We can add team features later

Has any of this changed? Sergey, what would need to be true for C to be better?"
Expected: Agent recalls decision reasoning
```

```
User: Sergey
Chat: "For C to be better... we'd need enterprise leads ready to close within our runway. Which clearly they're not, as Lead 2 proved.

You're right. I'm just nervous. One lost deal triggered my doubt. The logic still holds. I recommit to Option B."
Expected: Agent records Sergey recommitting
```

```
User: Vlad
Chat: "Save this discussion. Important to document that we revisited the decision at Week 5, Sergey had concerns about enterprise lead loss, team reaffirmed pivot decision, Sergey recommitted."
Expected: Agent saves recommitment
```

---

### Phase 8: Progress Check (Week 8)

#### Step 8.1: MVP launch
```
User: Kirill
Chat: "MVP is LIVE! Workfolio Beta:
- Client profiles ✓
- Project tracking linked to clients ✓
- Invoice generation ✓
- Time tracking ✓
- Payment status tracking ✓

Shipped in 7.5 weeks. Under estimate!"
Expected: Agent logs milestone
```

#### Step 8.2: Early results
```
User: Anya
Chat: "First week results:
- Invited 180 existing MAU to beta
- 92 tried new client features
- 34 created client profiles
- 8 sent invoices
- NPS survey: 42 (up from 28 before pivot!)

This is working!"
Expected: Agent logs positive metrics
```

```
User: Sergey
Chat: "I reached out to our 45 paying users about new features:
- 38 said invoicing is 'exactly what I needed'
- 12 already upgraded to higher tier ($20/month)
- 3 asked about team features (future roadmap)

I'm officially a believer now. Pivot was right call."
Expected: Agent logs Sergey's conversion
```

#### Step 8.3: Reflection
```
User: Vlad
Chat: "What a journey. 8 weeks ago we were debating pivot vs persevere.

Can you summarize how each person's position evolved through this process?"
Expected: Agent provides evolution summary:
- Vlad: Undecided → B (led consensus building)
- Kirill: A → B (data changed his mind)
- Anya: B throughout (product instinct)
- Mila: B leaning → B strong (competitive analysis)
- Sergey: C → B conditional → doubt → recommit B (sales reality)
```

#### Step 8.4: Lessons for future
```
User: Mila
Chat: "Save lessons from this pivot decision:
1. Give people time to research before deciding
2. Document positions - it's okay to change minds
3. Revisit decisions when doubt arises - it strengthens commitment
4. Data beats opinions but intuition matters too
5. Unanimous decisions are more powerful than 3-2 votes
6. Fast follow-through after decision (7.5 week build) maintains momentum"
Expected: Agent saves lessons learned
```

---

## Verification Queries

### Neo4j Checks
```cypher
// Position evolution
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'vote' OR k.content CONTAINS 'position' OR k.content CONTAINS 'Option'
RETURN k.content, k.ownerId, k.createdAt
ORDER BY k.createdAt;

// Arguments for each option
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'Option A' OR k.content CONTAINS 'Option B' OR k.content CONTAINS 'Option C'
RETURN k.content;

// Mind changes
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'changed' OR k.content CONTAINS 'convinced' OR k.content CONTAINS 'recommit'
RETURN k.content;

// Meeting summaries
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'meeting' OR k.content CONTAINS 'unanimous' OR k.content CONTAINS 'decided'
RETURN k.content ORDER BY k.createdAt;
```

---

## Expected Data Summary

After successful test:
- 5 users with distinct roles and perspectives
- 1 project
- Initial state of company saved
- 3 strategic options with pros/cons
- Multiple position statements per person
- Position changes tracked over time
- Research findings (leads, MVP scope, competition)
- 2+ meeting summaries
- Final unanimous decision with conditions
- Post-decision doubt and recommitment
- Brand name selection process
- MVP launch metrics
- Full decision evolution timeline

---

## Key Test Points

1. **Position tracking**: Who supported what option and when
2. **Mind changes**: Kirill A→B, Sergey C→B→doubt→B
3. **Argument recall**: "What were the arguments for enterprise?"
4. **Timeline queries**: "How did the team's position evolve?"
5. **Decision documentation**: Formal votes with conditions
6. **Doubt handling**: Revisiting decision without reverting
7. **Data-driven shifts**: Research changing positions

---

## Cleanup

```sql
DELETE FROM users WHERE email IN ('vlad@test.com', 'kirill@test.com', 'anya@test.com', 'sergey@test.com', 'mila@test.com');
```

```cypher
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
DETACH DELETE k;
```
