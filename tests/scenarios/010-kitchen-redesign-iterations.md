# Test Scenario 010: Kitchen Redesign - Multiple Iterations

## Overview

A couple (Igor and Sveta) redesigns their kitchen. This scenario tests:
- **Multiple design iterations** (3 complete redesigns)
- **Changing minds** and updating decisions
- **Disagreements** and compromise negotiations
- **Budget constraints** forcing revisits
- **Contractor feedback** changing plans

## Complexity: Medium (2 users) but HIGH iteration count

## Key Testing Focus
- Agent tracks decision CHANGES over time
- Agent can recall "what we decided before"
- Agent handles conflicting opinions
- Agent updates information without losing history

## Prerequisites

- Docker containers running (PostgreSQL, Neo4j, Qdrant)
- Backend running on http://localhost:8080
- Clean database

## Users

| Name  | Email           | Password |
|-------|----------------|----------|
| Igor  | igor@test.com  | test123  |
| Sveta | sveta@test.com | test123  |

## Test Execution

### Phase 1: Setup

#### Step 1.1: Register and create project
```
POST /api/auth/register
{ "email": "igor@test.com", "password": "test123", "name": "Igor" }
{ "email": "sveta@test.com", "password": "test123", "name": "Sveta" }

User: Igor
POST /api/projects { "name": "Kitchen Redesign 2025", "description": "Our dream kitchen" }
POST /api/projects/{projectId}/members { "email": "sveta@test.com" }
```

---

### Phase 2: Initial Vision (Iteration 1)

#### Step 2.1: Igor's vision
```
User: Igor
Chat: "Let's plan our new kitchen! My vision:
- Style: Modern minimalist
- Colors: All white with black accents
- Countertops: Black granite
- Cabinets: White high-gloss
- Appliances: All black (fridge, oven, dishwasher)
- Backsplash: White subway tiles
- Flooring: Gray tiles
Budget: 400,000 rubles"
Expected: Agent saves initial vision
```

#### Step 2.2: Sveta disagrees
```
User: Sveta
Chat: "Hmm, I don't like all white - it's too cold and clinical. I want:
- Style: Warm modern (not minimalist)
- Colors: Warm wood tones with green accents
- Countertops: Wooden or wood-look
- Cabinets: Natural oak
- Appliances: Stainless steel, not black
- Backsplash: Sage green tiles
- Some plants!

We need to discuss this."
Expected: Agent saves Sveta's alternative vision
```

#### Step 2.3: Discussion begins
```
User: Igor
Chat: "Wood countertops are impractical - they stain and need constant care. And green? Really? That's so outdated."
Expected: Agent logs disagreement
```

```
User: Sveta
Chat: "White kitchens are boring and show every speck of dirt! And black appliances look like an office. Green is actually very trendy now - look at Pinterest!"
Expected: Agent logs response
```

#### Step 2.4: First compromise attempt
```
User: Igor
Chat: "Okay, let's find middle ground. What if:
- Cabinets: White on top, wood-look on bottom?
- Countertops: Quartz that looks like marble (not wood, not granite)
- Appliances: Stainless steel (I can agree to this)
- Backsplash: White, but not subway tiles - something more interesting?"
Expected: Agent records compromise proposal
```

```
User: Sveta
Chat: "I like the two-tone cabinets idea! But I still want some color. What about:
- Upper cabinets: Sage green (not white!)
- Lower cabinets: Natural oak
- Countertops: Quartz is fine
- Backsplash: Terracotta or warm beige tiles

No white walls please - it's so sterile."
Expected: Agent records counter-proposal
```

#### Step 2.5: Iteration 1 decision
```
User: Igor
Chat: "Fine, let's try the green. Save this as our Version 1 design:
- Upper cabinets: Sage green
- Lower cabinets: Natural oak
- Countertops: White quartz with gray veining
- Backsplash: Terracotta hexagon tiles
- Appliances: Stainless steel
- Flooring: Wood-look tiles
- Walls: Warm white (not pure white)
Budget: 400,000 rubles

Let's get quotes with this."
Expected: Agent saves Version 1 design
```

---

### Phase 3: Reality Check (Contractor Quotes)

#### Step 3.1: First quote shock
```
User: Sveta
Chat: "Got quote from KitchenPro:
- Custom oak cabinets: 280,000 rubles
- Sage green uppers (custom color): 120,000 rubles
- Quartz countertops: 85,000 rubles
- Terracotta tiles: 35,000 rubles
- Installation: 80,000 rubles
- Appliances: ~150,000 rubles

TOTAL: 750,000 rubles!!!

We're 350,000 over budget. What do we do?"
Expected: Agent records quote and budget problem
```

#### Step 3.2: Igor's reaction
```
User: Igor
Chat: "I told you custom colors are expensive! The sage green cabinets alone are 120k. If we went with standard white, it would be half that."
Expected: Agent logs argument
```

```
User: Sveta
Chat: "Don't blame the green! The oak cabinets are 280k - that's the main cost. Maybe we need to compromise on cabinet material, not color."
Expected: Agent logs counter-argument
```

#### Step 3.3: Budget discussion
```
User: Igor
Chat: "Options to reduce cost:
1. Standard white upper cabinets instead of sage green: save 60,000
2. MDF with oak veneer instead of solid oak: save 100,000
3. Laminate countertops instead of quartz: save 50,000
4. Simpler backsplash: save 20,000

What are you willing to sacrifice?"
Expected: Agent records cost-saving options
```

```
User: Sveta
Chat: "NOT the color - that's the whole personality! I'd rather:
- Option 2: MDF is fine if it looks good
- Keep quartz - laminate looks cheap
- Simpler backsplash okay

But even with these we're still over budget..."
Expected: Agent records preferences
```

#### Step 3.4: More quotes needed
```
User: Igor
Chat: "Let's get more quotes. What were the other options we saved?"
Expected: Agent recalls Version 1 design details
```

---

### Phase 4: Iteration 2 - Revised Design

#### Step 4.1: Second quote
```
User: Sveta
Chat: "Quote from BudgetKitchens:
- IKEA cabinet frames + custom fronts: 180,000 total
- They can do sage green!
- Quartz countertops: 70,000 (different supplier)
- Simple white subway backsplash: 15,000
- Installation: 60,000
Total without appliances: 325,000

Much better! But... they say sage green with oak might clash. They suggest sage green with white or gray base."
Expected: Agent records new quote and suggestion
```

#### Step 4.2: Color debate reopens
```
User: Igor
Chat: "See! Professional says green and oak clash. Let's do sage green uppers with gray lower cabinets."
Expected: Agent records suggestion
```

```
User: Sveta
Chat: "But I loved the warm oak look! The green was YOUR compromise, remember? Originally I wanted oak everywhere."
Expected: Agent should recall original positions
```

```
User: Igor
Chat: "What did we each originally want? I can't remember anymore."
Expected: Agent recalls:
- Igor: White minimalist with black granite
- Sveta: Warm wood tones with green accents
```

#### Step 4.3: New compromise
```
User: Sveta
Chat: "Okay, what about this - what if we go warmer gray? Like greige (gray-beige)? That would work with both sage green AND feel warm."
Expected: Agent records suggestion
```

```
User: Igor
Chat: "Greige could work. So Version 2:
- Upper cabinets: Sage green
- Lower cabinets: Greige (warm gray)
- Countertops: White quartz
- Backsplash: Simple white subway (for budget)
- Appliances: Stainless steel

What do you think?"
Expected: Agent saves Version 2
```

```
User: Sveta
Chat: "I miss the wood element though. Can we add open wooden shelves somewhere? Like 2-3 floating shelves for plants and nice dishes?"
Expected: Agent records addition
```

```
User: Igor
Chat: "Good idea! Add 3 oak floating shelves to Version 2. Maybe above the sink area?"
Expected: Agent updates Version 2
```

---

### Phase 5: Seeing Samples (Mind Changes Again)

#### Step 5.1: Showroom visit
```
User: Sveta
Chat: "Visited the showroom today. Bad news... the sage green sample looks different than the pictures. In real life it looks more gray-green, almost like a hospital color. I don't love it anymore 😢"
Expected: Agent records opinion change
```

```
User: Igor
Chat: "Oh no, we based everything on that color! What now? Back to square one?"
Expected: Agent logs concern
```

#### Step 5.2: Alternative colors discovered
```
User: Sveta
Chat: "BUT - I found this gorgeous deep forest green! It's called 'Emerald Night'. More dramatic but SO beautiful. Also saw a dusty pink that's surprisingly nice with wood."
Expected: Agent records new options
```

```
User: Igor
Chat: "Pink?! Absolutely not. I could consider the forest green but won't it make the kitchen dark?"
Expected: Agent records objection
```

```
User: Sveta
Chat: "What if forest green is only on the island? And we do cream/off-white for the wall cabinets? The showroom had exactly this combo - I took photos."
Expected: Agent records new idea
```

#### Step 5.3: New direction discussion
```
User: Igor
Chat: "Wait, do we even have room for an island? Our kitchen is only 12 sq meters."
Expected: Agent prompts practical discussion
```

```
User: Sveta
Chat: "Good point. The designer at the showroom said minimum 15 sq meters for a real island. She suggested a peninsula instead - attached to the wall but gives the same effect."
Expected: Agent records constraint
```

```
User: Igor
Chat: "Peninsula could work. But this is a completely different design now. What's our current plan vs original?"
Expected: Agent should compare versions:
- Original (Igor): White minimalist, black accents
- Original (Sveta): Oak wood, green accents
- Version 1: Sage green + oak + terracotta (over budget)
- Version 2: Sage green + greige + oak shelves
- Now discussing: Forest green peninsula + cream cabinets
```

---

### Phase 6: Iteration 3 - Final Design

#### Step 6.1: Version 3 proposal
```
User: Sveta
Chat: "Let me propose Version 3:
- Wall cabinets: Cream/off-white (warm, not cold white!)
- Base cabinets: Cream/off-white
- Peninsula: Forest green 'Emerald Night'
- Countertops: Butcher block on peninsula, quartz elsewhere
- Backsplash: Handmade-look white tiles with texture
- Open shelving: 3 oak floating shelves (we both liked this)
- Appliances: Stainless steel
- Add: Brass/gold hardware for warmth

This gives drama (green peninsula), warmth (wood accents, brass), and stays practical (mostly light colors)"
Expected: Agent saves Version 3
```

#### Step 6.2: Igor's concerns
```
User: Igor
Chat: "I like it conceptually, but:
1. Butcher block on peninsula - won't it get damaged from food prep?
2. Brass hardware - isn't that going to look dated in 5 years?
3. What about budget?"
Expected: Agent records concerns
```

```
User: Sveta
Chat: "Good points:
1. Peninsula can be for eating/socializing, prep area on quartz counter
2. Brass is classic, not trendy - been around 100 years. But we can do matte black if you prefer?
3. Budget - let's get a quote before worrying"
Expected: Agent records responses
```

#### Step 6.3: Hardware debate
```
User: Igor
Chat: "You know what, the more I think about it, matte black hardware would look amazing with the forest green. Very sophisticated."
Expected: Agent records preference change
```

```
User: Sveta
Chat: "Hmm, now I'm unsure. Black might be too harsh with cream cabinets. What about brushed nickel? It's between brass and black."
Expected: Agent records uncertainty
```

```
User: Igor
Chat: "Let's decide this later - hardware is easy to change. For now put 'hardware TBD - considering brass, matte black, or brushed nickel'"
Expected: Agent saves with TBD
```

#### Step 6.4: Finalizing Version 3
```
User: Sveta
Chat: "Updated Version 3 design:
- Wall cabinets: Cream ('Antique White')
- Base cabinets: Cream ('Antique White')
- Peninsula: Forest green ('Emerald Night')
- Countertops: Quartz (main), butcher block (peninsula only)
- Backsplash: Zellige-style white tiles
- Shelving: 3 oak floating shelves above coffee station
- Hardware: TBD (brass/black/nickel)
- Appliances: Stainless steel
- Layout: L-shape + peninsula

Save as Version 3 Final Draft"
Expected: Agent saves Version 3 Final
```

---

### Phase 7: Final Quote & Last Minute Changes

#### Step 7.1: Version 3 quote
```
User: Igor
Chat: "Quote for Version 3:
- Cabinets (IKEA + custom fronts): 195,000
- Peninsula in green: 45,000
- Quartz countertops: 65,000
- Butcher block for peninsula: 12,000
- Zellige tiles + installation: 40,000
- Floating shelves: 8,000
- Installation labor: 55,000
Subtotal: 420,000

Appliances: 130,000

TOTAL: 550,000 rubles

Still 150,000 over our 400k budget but much better than 750k!"
Expected: Agent records quote
```

#### Step 7.2: Budget negotiation
```
User: Sveta
Chat: "Options:
1. Increase budget to 550k (take small loan?)
2. Phase the project - do cabinets now, peninsula later
3. Find more savings somewhere

I vote for increasing budget - we live here every day and will for 10+ years."
Expected: Agent records options
```

```
User: Igor
Chat: "I don't want a loan for kitchen. What if we:
- Skip peninsula for now (save 45k + 12k = 57k)
- Get standard quartz instead of premium (save 15k)
- DIY the floating shelves (save 5k)

That's 77k savings = 473k total. We can add peninsula next year."
Expected: Agent records counter-proposal
```

#### Step 7.3: Sveta's reaction
```
User: Sveta
Chat: "But the peninsula IS the design! Without it, we just have a cream kitchen. Boring! The green peninsula is what makes it special.

What if we finance just the peninsula portion? 45k over 12 months is only 4k/month."
Expected: Agent records emotional response
```

```
User: Igor
Chat: "I understand it's the centerpiece. Fine, let's do the 550k but:
1. We skip vacation this summer (saves ~100k)
2. No other big purchases for 6 months
3. We sell the old kitchen cabinets

Deal?"
Expected: Agent records compromise conditions
```

```
User: Sveta
Chat: "Deal! Worth it for our dream kitchen. Save this as FINAL decision with the conditions."
Expected: Agent saves final decision
```

---

### Phase 8: Very Last Minute Change

#### Step 8.1: Night before signing
```
User: Igor
Chat: "Can't sleep. Looking at Version 3 again. The cream cabinets... are they too yellow? Now I'm second-guessing. Everyone has white kitchens for a reason - they're timeless."
Expected: Agent records doubt
```

```
User: Sveta
Chat: "It's 2am, go to sleep! We've been through this. Remember why we rejected white? It was 'cold and clinical' - YOUR words originally!"
Expected: Agent recalls Igor's original objection to white
```

```
User: Igor
Chat: "You're right. Just pre-signing nerves. Cream is the right choice. The green peninsula will look amazing. Sorry for the panic."
Expected: Agent records resolution
```

#### Step 8.2: Contract signed
```
User: Sveta
Chat: "Contract signed! 🎉 Final price: 545,000 (negotiated 5k off).
Start date: February 15
Completion: March 15 (4 weeks)
Hardware decision needed by Feb 10

We did it! After how many design versions?"
Expected: Agent recalls: 3 major versions plus variations
```

---

### Phase 9: Post-Decision Review

#### Step 9.1: Decision journey
```
User: Igor
Chat: "Summarize our entire design journey - what changed from beginning to now?"
Expected: Agent provides comprehensive summary:
- Started: Igor wanted minimalist white/black, Sveta wanted warm wood/green
- Key conflicts: Color temperature, budget, practicality
- Major iterations: 3 versions
- Final compromise: Cream + forest green peninsula + wood accents
- Budget: 400k → 545k (36% over)
- Key compromises made by each person
```

#### Step 9.2: Lessons learned
```
User: Sveta
Chat: "What should we remember for next renovation project?"
Expected: Agent could suggest:
- Get quotes BEFORE falling in love with a design
- Visit showrooms to see real colors
- Budget padding: plan for 30%+ overage
- Take photos of samples
- Sleep on big decisions
- Document why you rejected options
```

---

### Phase 10: Hardware Final Decision

#### Step 10.1: Still undecided
```
User: Sveta
Chat: "Feb 5. We need to decide hardware by Feb 10! Current options:
- Brass: Warm, classic, matches oak shelves
- Matte black: Modern, matches appliances
- Brushed nickel: Neutral, safe choice

I've changed my mind 3 times this week. What were our arguments for each?"
Expected: Agent recalls hardware discussion history
```

#### Step 10.2: Final hardware debate
```
User: Igor
Chat: "Let's just decide. I vote matte black - it ties in the stainless appliances and won't look dated."
Expected: Agent records vote
```

```
User: Sveta
Chat: "But brass ties in the wood shelves and adds warmth... Ugh. Okay, what if we do BOTH? Brass on upper cabinets, black on lower?"
Expected: Agent records creative solution
```

```
User: Igor
Chat: "Mixed hardware? Is that even done?"
Expected: Agent records question
```

```
User: Sveta
Chat: "Yes! It's a design trend. Upper and lower can be different. The designer mentioned it. Let's do brass uppers, black lowers. Final answer!"
Expected: Agent records final decision
```

```
User: Igor
Chat: "Sure, let's try it. If we hate it, hardware is easy to swap later. Save hardware decision: Brass on upper cabinets, matte black on base cabinets and peninsula."
Expected: Agent saves final hardware decision
```

---

## Verification Queries

### Neo4j Checks
```cypher
// All design versions
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'Version' OR k.content CONTAINS 'design'
RETURN k.content, k.createdAt
ORDER BY k.createdAt;

// Decision changes
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'changed' OR k.content CONTAINS 'instead' OR k.content CONTAINS 'originally'
RETURN k.content;

// Disagreements
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'disagree' OR k.content CONTAINS 'don\'t like' OR k.content CONTAINS 'but'
RETURN k.content;

// Budget evolution
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'rubles' OR k.content CONTAINS 'budget'
RETURN k.content ORDER BY k.createdAt;
```

---

## Expected Data Summary

After successful test:
- 2 users
- 1 project
- 3+ design versions with full specs
- Multiple opinion/preference changes tracked
- Budget evolution (400k → 750k → 545k)
- Disagreement and resolution history
- Final decisions with rationale

---

## Key Test Points

1. **Version tracking**: Can recall Version 1, 2, 3 details
2. **Opinion changes**: Tracks when people change minds
3. **Conflict history**: Records disagreements and resolutions
4. **Decision recall**: "What did we originally decide about X?"
5. **Comparison queries**: "What changed from Version 1 to Version 3?"
6. **Budget tracking**: Tracks multiple quotes and budget discussions
7. **TBD handling**: Some decisions left open, then closed later

---

## Cleanup

```sql
DELETE FROM users WHERE email IN ('igor@test.com', 'sveta@test.com');
```

```cypher
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
DETACH DELETE k;
```
