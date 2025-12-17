# Test Scenario 007: Room Renovation

## Overview

Three roommates (Kostya, Denis, Artem) renovate their shared living room. They:
1. Plan renovation phases
2. Track materials and costs
3. Hire and manage contractors
4. Handle decisions and change requests
5. Document before/after

## Complexity: Medium (3 users)

## Prerequisites

- Docker containers running (PostgreSQL, Neo4j, Qdrant)
- Backend running on http://localhost:8080
- Clean database (or isolated test data)

## Users

| Name   | Email            | Password |
|--------|-----------------|----------|
| Kostya | kostya@test.com | test123  |
| Denis  | denis@test.com  | test123  |
| Artem  | artem@test.com  | test123  |

## Test Execution

### Phase 1: Setup

#### Step 1.1: Register users
```
POST /api/auth/register
{ "email": "kostya@test.com", "password": "test123", "name": "Kostya" }
{ "email": "denis@test.com", "password": "test123", "name": "Denis" }
{ "email": "artem@test.com", "password": "test123", "name": "Artem" }
```

#### Step 1.2: Create project
```
User: Kostya
POST /api/projects { "name": "Living Room Renovation", "description": "January 2025 remodel" }
```

#### Step 1.3: Add roommates
```
User: Kostya
POST /api/projects/{projectId}/members { "email": "denis@test.com" }
POST /api/projects/{projectId}/members { "email": "artem@test.com" }
```

---

### Phase 2: Initial Planning

#### Step 2.1: Room assessment
```
User: Kostya
Chat: "Living room renovation plan. Room size: 25 sq meters. Current state:
- Wallpaper: old, peeling in corners
- Floor: laminate, scratched badly
- Ceiling: has water stain from old leak (fixed)
- Windows: 2, good condition
- Door: squeaky, needs adjusting
- Electrical: only 4 outlets, need more
Goal: Modern minimalist style, gray/white palette"
Expected: Agent saves room assessment
```

#### Step 2.2: Budget planning
```
User: Denis
Chat: "Total renovation budget: 150,000 rubles, split 3 ways = 50,000 each.
Budget breakdown:
- Flooring: 40,000
- Walls (paint): 15,000
- Ceiling: 10,000
- Electrical work: 25,000
- Furniture: 45,000
- Decor & lighting: 15,000"
Expected: Agent saves budget
```

#### Step 2.3: Timeline
```
User: Artem
Chat: "Renovation timeline:
- Week 1 (Jan 6-12): Demolition, electrical work
- Week 2 (Jan 13-19): Ceiling and walls
- Week 3 (Jan 20-26): Flooring
- Week 4 (Jan 27-Feb 2): Furniture, finishing touches
We need to be done by Feb 2 - that's the Super Bowl party!"
Expected: Agent saves timeline
```

---

### Phase 3: Material Selection

#### Step 3.1: Flooring decision
```
User: Kostya
Chat: "Flooring options we discussed:
1. Laminate - 25,000 rubles (budget option)
2. Engineered hardwood - 40,000 (our budget)
3. SPC vinyl - 35,000 (waterproof)

I vote for engineered hardwood - looks best"
Expected: Agent saves options
```

#### Step 3.2: Denis votes
```
User: Denis
Chat: "I vote for SPC vinyl flooring. It's waterproof and we won't worry about spills"
Expected: Agent records vote
```

#### Step 3.3: Artem decides
```
User: Artem
Chat: "I'm with Denis on the vinyl. 2 vs 1, let's go with SPC vinyl flooring for 35,000"
Expected: Agent records decision: SPC vinyl chosen
```

#### Step 3.4: Wall paint decision
```
User: Kostya
Chat: "Wall paint: agreed on Dulux 'Gray Cashmere' for main walls and white for ceiling. Need 10 liters gray, 5 liters white.
Gray: 3500/can (3 cans) = 10,500
White: 2500/can (2 cans) = 5,000
Total paint: 15,500"
Expected: Agent records decision
```

#### Step 3.5: Electrical planning
```
User: Denis
Chat: "Electrical plan:
- Add 6 new outlets (total 10)
- Install dimmer switch for main light
- Add LED strip behind TV area
- New chandelier + 2 wall sconces
Electrician quote: 18,000 for work
Materials estimate: 7,000
Total electrical: 25,000"
Expected: Agent saves plan
```

---

### Phase 4: Contractor Management

#### Step 4.1: Finding contractors
```
User: Kostya
Chat: "Contractor research:
1. 'RemontPro' - good reviews, quote 45,000 (walls + ceiling + flooring)
2. 'MasterDom' - cheaper at 38,000 but mixed reviews
3. Individual workers via Avito - risky but 30,000

I recommend RemontPro despite higher cost"
Expected: Agent saves options
```

#### Step 4.2: Contractor chosen
```
User: Denis
Chat: "We all agreed on RemontPro. Booked for January 6 start. Contact: Mikhail +7-999-777-8888. Deposit paid: 15,000"
Expected: Agent records hiring decision
```

#### Step 4.3: Electrician hired
```
User: Artem
Chat: "Hired electrician Sergey separately (more specialized). Start: Jan 6, works parallel with demo. Cost: 18,000. Contact: +7-999-666-5555. Deposit: 5,000"
Expected: Agent records electrician
```

---

### Phase 5: Work Progress Week 1

#### Step 5.1: Day 1 - Demo start
```
User: Kostya
Chat: "Jan 6: Work started! Old laminate removed, wallpaper stripped. Found issue: subfloor has some uneven spots - needs leveling. Extra cost: 3,000"
Expected: Agent logs progress and issue
```

#### Step 5.2: Day 2 - Electrical
```
User: Denis
Chat: "Jan 7: Electrician cutting channels for new wiring. Dust everywhere but progress is good. All furniture moved to bedrooms."
Expected: Agent logs progress
```

#### Step 5.3: Day 3 - Decision needed
```
User: Artem
Chat: "Jan 8: Workers found old wiring behind wall - aluminum, not copper. Electrician strongly recommends replacing ALL wiring for safety. Extra cost: 12,000. We need to decide today!"
Expected: Agent logs urgent decision needed
```

#### Step 5.4: Emergency decision
```
User: Kostya
Chat: "Emergency vote on rewiring. I say yes - safety first"
Expected: Agent records vote
```

#### Step 5.5: Denis votes
```
User: Denis
Chat: "Yes to rewiring. Let's take 4,000 each from emergency funds"
Expected: Agent records vote
```

#### Step 5.6: Artem confirms
```
User: Artem
Chat: "Unanimous yes. Told electrician to proceed with full rewiring. New budget for electrical: 25,000 + 12,000 = 37,000. Updating total budget to 162,000"
Expected: Agent updates budget, records decision
```

#### Step 5.7: Week 1 summary
```
User: Kostya
Chat: "Week 1 complete:
✓ Demo done
✓ New wiring installed
✓ Subfloor leveled
✓ Electrical boxes in place
Next week: ceiling and walls"
Expected: Agent saves progress
```

---

### Phase 6: Work Progress Week 2

#### Step 6.1: Ceiling work
```
User: Denis
Chat: "Jan 13: Ceiling patched and primed. Water stain fully covered. Looks great!"
Expected: Agent logs progress
```

#### Step 6.2: Wall painting
```
User: Artem
Chat: "Jan 15: First coat of gray on walls. Color looks darker than expected. Should we continue or change?"
Expected: Agent logs issue and question
```

#### Step 6.3: Color decision
```
User: Kostya
Chat: "Looked at the walls - second coat will be lighter. Contractor confirmed. Let's stick with it."
Expected: Agent records decision to continue
```

#### Step 6.4: Week 2 complete
```
User: Denis
Chat: "Jan 19: Ceiling done (white, perfect), walls done (2 coats gray), looks amazing! Paint cost actual: 14,800 (under budget by 700)"
Expected: Agent saves progress and cost
```

---

### Phase 7: Work Progress Week 3

#### Step 7.1: Flooring installation
```
User: Artem
Chat: "Jan 20: Vinyl flooring installation started. Color: 'Natural Oak'. Workers say 2 days needed."
Expected: Agent logs progress
```

#### Step 7.2: Flooring issue
```
User: Kostya
Chat: "Jan 21: Flooring issue - we're 2 sq meters short! Material miscalculation. Need to buy more. Same batch available for 3,200"
Expected: Agent logs issue and cost
```

#### Step 7.3: Materials bought
```
User: Denis
Chat: "Got the extra flooring. Total flooring cost: 35,000 + 3,200 = 38,200"
Expected: Agent updates cost
```

#### Step 7.4: Week 3 complete
```
User: Artem
Chat: "Jan 25: Flooring DONE! Looks incredible. Also installed:
- All 10 outlets working
- Dimmer switch installed
- LED strip behind TV area ready
Electrical work complete!"
Expected: Agent saves progress
```

---

### Phase 8: Finishing Touches Week 4

#### Step 8.1: Furniture shopping
```
User: Kostya
Chat: "Furniture bought:
- New sofa (gray, IKEA Kivik): 29,990
- Coffee table: 5,990
- TV stand: 8,990
Total furniture: 44,970"
Expected: Agent records purchases
```

#### Step 8.2: Lighting installed
```
User: Denis
Chat: "Lighting installed:
- Main chandelier (modern, matte black): 6,500
- 2 wall sconces: 3,800
- LED strip was 2,200
Total lighting: 12,500"
Expected: Agent records costs
```

#### Step 8.3: Final decor
```
User: Artem
Chat: "Final touches:
- New curtains: 4,500
- 2 throw pillows: 1,800
- Wall art (abstract print): 3,500
- Plants: 2,200
Total decor: 12,000"
Expected: Agent records costs
```

#### Step 8.4: Before/after comparison
```
User: Kostya
Chat: "Save these notes for our before/after comparison:

BEFORE:
- Peeling wallpaper
- Scratched laminate
- Water-stained ceiling
- Only 4 outlets
- Old lighting

AFTER:
- Fresh gray paint
- Beautiful vinyl flooring
- Perfect white ceiling
- 10 outlets + LED strip
- Modern lighting fixtures
- New furniture"
Expected: Agent saves comparison
```

---

### Phase 9: Final Budget & Payment

#### Step 9.1: Final budget check
```
User: Denis
Chat: "Give me the complete breakdown of what we spent"
Expected: Agent calculates:
- Flooring: 38,200
- Paint: 14,800
- Electrical (work): 30,000 (18k + 12k rewiring)
- Electrical (materials): 7,000
- Contractor (RemontPro): 45,000
- Subfloor leveling: 3,000
- Furniture: 44,970
- Lighting: 12,500
- Decor: 12,000
Total: 207,470 rubles
```

#### Step 9.2: Cost per person
```
User: Artem
Chat: "How much does each of us owe?"
Expected: Agent calculates: 207,470 / 3 = 69,157 rubles each
```

#### Step 9.3: Payments made
```
User: Kostya
Chat: "Payment tracking - we each put in 50,000 initially. We need 19,157 more from each person.
I've paid my extra share."
Expected: Agent tracks payments
```

#### Step 9.4: Contractor payment
```
User: Denis
Chat: "Paid RemontPro final balance: 30,000 (45,000 - 15,000 deposit). Got receipt."
Expected: Agent records payment
```

#### Step 9.5: Electrician payment
```
User: Artem
Chat: "Paid electrician Sergey remaining 25,000 (30,000 - 5,000 deposit). All contractors paid!"
Expected: Agent records payment
```

---

### Phase 10: Project Completion

#### Step 10.1: Lessons learned
```
User: Kostya
Chat: "Save these lessons for future renovations:
1. Always add 15% to material estimates
2. Check old wiring BEFORE starting
3. Get multiple contractor quotes
4. Document everything with photos
5. Gray paint looks darker wet - trust the process"
Expected: Agent saves lessons
```

#### Step 10.2: Final status
```
User: Denis
Chat: "Is everything on our renovation done? Any open tasks?"
Expected: Agent confirms all complete
```

#### Step 10.3: Success!
```
User: Artem
Chat: "Super Bowl party was a huge success! Everyone loved the new room. Project complete! 🎉"
Expected: Agent marks project complete, saves celebration note
```

---

## Verification Queries

### Neo4j Checks
```cypher
// All decisions
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'decided' OR k.content CONTAINS 'vote' OR k.content CONTAINS 'agreed'
RETURN k.content, k.createdAt;

// Budget items
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'rubles' OR k.content CONTAINS 'cost' OR k.content CONTAINS 'paid'
RETURN k.content;

// Timeline/progress
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'Jan' OR k.content CONTAINS 'Week'
RETURN k.content ORDER BY k.createdAt;

// Issues and changes
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'issue' OR k.content CONTAINS 'problem' OR k.content CONTAINS 'extra'
RETURN k.content;
```

---

## Expected Data Summary

After successful test:
- 3 users
- 1 project
- Room specifications
- Budget allocations and actuals
- Material decisions with voting history
- 2 contractor records
- Week-by-week progress logs
- Issues and resolutions
- Final cost breakdown
- Lessons learned

---

## Key Test Points

1. **Decision tracking**: Record votes and final decisions
2. **Budget changes**: Handle unexpected costs, update totals
3. **Timeline logging**: Track progress by date
4. **Issue resolution**: Log problems and solutions
5. **Cost calculations**: Split expenses among roommates
6. **Before/after**: Store comparison data

---

## Cleanup

```sql
DELETE FROM users WHERE email IN ('kostya@test.com', 'denis@test.com', 'artem@test.com');
```

```cypher
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
DETACH DELETE k;
```
