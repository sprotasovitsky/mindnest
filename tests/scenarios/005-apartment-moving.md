# Test Scenario 005: Moving to New Apartment

## Overview

A family of three (Pavel - husband, Anya - wife, Grandma Vera) moves to a new apartment. They:
1. Create inventory of items by room
2. Assign packing tasks
3. Coordinate moving day logistics
4. Track what's packed and what's unpacked
5. Handle address changes and utilities

## Complexity: Medium (3 users)

## Prerequisites

- Docker containers running (PostgreSQL, Neo4j, Qdrant)
- Backend running on http://localhost:8080
- Clean database (or isolated test data)

## Users

| Name  | Email           | Password |
|-------|----------------|----------|
| Pavel | pavel@test.com | test123  |
| Anya  | anya@test.com  | test123  |
| Vera  | vera@test.com  | test123  |

## Test Execution

### Phase 1: Setup

#### Step 1.1: Register users
```
POST /api/auth/register
{ "email": "pavel@test.com", "password": "test123", "name": "Pavel" }
{ "email": "anya@test.com", "password": "test123", "name": "Anya" }
{ "email": "vera@test.com", "password": "test123", "name": "Vera" }
```

#### Step 1.2: Pavel creates project
```
User: Pavel
POST /api/projects { "name": "Moving to New Apartment", "description": "January 2025 move" }
```

#### Step 1.3: Add family members
```
User: Pavel
POST /api/projects/{projectId}/members { "email": "anya@test.com" }
POST /api/projects/{projectId}/members { "email": "vera@test.com" }
```

---

### Phase 2: Move Planning

#### Step 2.1: Key dates
```
User: Pavel
Chat: "We're moving on January 15th. Key dates to remember:
- January 10: Start packing
- January 14: Movers arrive at 9am
- January 15: Final move, keys handover at 3pm
- January 20: Old apartment final cleaning
New address: Tverskaya 25, apt 42"
Expected: Agent saves dates and address
```

#### Step 2.2: Moving company
```
User: Anya
Chat: "Booked 'GruzovichkoF' moving company. Cost: 25000 rubles. Contact: +7-999-123-4567, manager Sergey. They provide 3 movers and a truck."
Expected: Agent saves moving company details
```

---

### Phase 3: Room Inventory

#### Step 3.1: Living room inventory
```
User: Anya
Chat: "Living room inventory:
- Sofa (large, needs 2 people)
- TV 55 inch + TV stand
- Coffee table
- 2 armchairs
- Bookshelf with ~100 books
- Floor lamp
- Curtains
- 3 paintings
Label all boxes: LR-1, LR-2, etc."
Expected: Agent saves inventory
```

#### Step 3.2: Kitchen inventory
```
User: Anya
Chat: "Kitchen inventory:
- Refrigerator (movers handle)
- Washing machine (movers handle)
- Microwave
- Box of pots and pans
- Box of dishes
- Box of utensils
- Small appliances (kettle, toaster, blender)
Label: K-1, K-2, etc."
Expected: Agent saves inventory
```

#### Step 3.3: Bedroom inventory
```
User: Pavel
Chat: "Master bedroom:
- Queen bed + mattress
- 2 nightstands
- Wardrobe (disassemble!)
- Dresser
- 4 boxes of clothes
- 2 boxes of linens
Label: BR-1, BR-2, etc."
Expected: Agent saves inventory
```

#### Step 3.4: Grandma's room
```
User: Vera
Chat: "My room items:
- Single bed
- Small wardrobe
- Desk
- Chair
- 2 boxes of personal items
- Medicine cabinet (fragile!)
- Icon corner items - pack separately, very carefully
Label: GR-1, GR-2, etc."
Expected: Agent saves inventory
```

#### Step 3.5: Other items
```
User: Pavel
Chat: "Bathroom and misc:
- 2 boxes bathroom items
- Vacuum cleaner
- Ironing board
- 3 suitcases (use for clothes)
- 5 boxes of random stuff
Label: MISC-1, MISC-2, etc."
Expected: Agent saves inventory
```

---

### Phase 4: Task Assignment

#### Step 4.1: Create packing tasks
```
User: Pavel
Chat: "Create packing tasks with deadline January 13:
- Task for Anya: Pack kitchen (boxes K-1 to K-5)
- Task for Anya: Pack living room decorations and books
- Task for Pavel: Disassemble wardrobe and bed
- Task for Pavel: Pack all boxes from bedroom
- Task for Vera: Pack your room carefully
- Task for Pavel: Disconnect and prep appliances"
Expected: Agent creates 6 tasks
```

#### Step 4.2: Administrative tasks
```
User: Anya
Chat: "Administrative tasks (deadline January 20):
- Task for Anya: Notify postal service of address change
- Task for Anya: Update address at work
- Task for Pavel: Transfer internet to new address
- Task for Pavel: Update car registration address
- Task for Pavel: Arrange utility meter readings"
Expected: Agent creates 5 tasks
```

---

### Phase 5: Packing Progress

#### Step 5.1: Anya packs kitchen
```
User: Anya
Chat: "Kitchen packing done! 5 boxes total:
- K-1: Pots and pans
- K-2: Dishes
- K-3: Utensils and small items
- K-4: Small appliances
- K-5: Food items (non-perishable)
Mark my kitchen task complete."
Expected: Agent records boxes and marks task done
```

#### Step 5.2: Check packing status
```
User: Pavel
Chat: "What's the status of all packing tasks?"
Expected: Agent shows:
- Kitchen: DONE (Anya)
- Living room: pending
- Wardrobe disassembly: pending
- Bedroom boxes: pending
- Vera's room: pending
- Appliances: pending
```

#### Step 5.3: Vera's progress
```
User: Vera
Chat: "I've packed my personal items - 2 boxes GR-1 and GR-2. The icons are in a special box GR-3, wrapped in soft cloth. Medicine cabinet in GR-4. Still need help with furniture."
Expected: Agent records progress
```

#### Step 5.4: Pavel's progress
```
User: Pavel
Chat: "Done with:
- Disassembled wardrobe (4 parts + hardware bag)
- Disassembled bed frame
- Packed 4 boxes of clothes (BR-1 to BR-4)
- Packed linens (BR-5, BR-6)
- Disconnected washing machine
Mark my furniture and bedroom tasks complete."
Expected: Agent marks tasks done
```

#### Step 5.5: Anya finishes living room
```
User: Anya
Chat: "Living room packed:
- LR-1, LR-2: Books (heavy!)
- LR-3: Paintings (marked fragile)
- LR-4: Decorations and curtains
- LR-5: Electronics and cables
Done!"
Expected: Agent records and marks task done
```

---

### Phase 6: Moving Day Coordination

#### Step 6.1: Morning check
```
User: Pavel
Chat: "Moving day January 14. Movers confirmed for 9am. Total boxes to move: how many?"
Expected: Agent counts: K-5 + BR-6 + GR-4 + LR-5 + MISC-5 = ~25 boxes plus furniture
```

#### Step 6.2: Priority items
```
User: Anya
Chat: "Mark these as FIRST to unload at new place:
- Kitchen box K-2 (dishes for first meal)
- Kettle from K-4
- Bathroom essentials
- Vera's medicine cabinet GR-4"
Expected: Agent marks priority items
```

#### Step 6.3: Movers update
```
User: Pavel
Chat: "Movers arrived at 9:15. Truck loading started. Large items going first: refrigerator, washing machine, sofa, beds."
Expected: Agent logs timeline
```

#### Step 6.4: Arrival at new place
```
User: Pavel
Chat: "Arrived at new apartment at 1pm. Started unloading. Noting issue: small scratch on wardrobe door from moving."
Expected: Agent records arrival and issue
```

---

### Phase 7: Unpacking at New Place

#### Step 7.1: First day unpacking
```
User: Anya
Chat: "Unpacked today:
- Kitchen boxes K-1 to K-5 - all done
- Connected refrigerator
- Set up kettle and microwave
Kitchen functional!"
Expected: Agent updates status
```

#### Step 7.2: Vera settled
```
User: Vera
Chat: "My room is set up. Bed assembled, wardrobe in place. Icons on the wall. Medicine cabinet accessible. Thank you all!"
Expected: Agent records completion
```

#### Step 7.3: Remaining unpacking
```
User: Pavel
Chat: "What's still packed/not set up?"
Expected: Agent lists remaining:
- Living room furniture arrangement
- TV mounting
- Bookshelf setup
- Some MISC boxes
```

---

### Phase 8: Administrative Completion

#### Step 8.1: Anya's admin tasks
```
User: Anya
Chat: "Done with my admin tasks:
- Notified postal service - mail forwarding set up
- Updated work address in HR system
Mark both complete."
Expected: Agent marks tasks done
```

#### Step 8.2: Pavel's admin tasks
```
User: Pavel
Chat: "My admin tasks done:
- Internet transferred, technician coming January 17
- Car registration updated online
- Final meter readings submitted to old utility company
All admin tasks complete!"
Expected: Agent marks tasks done
```

#### Step 8.3: Final summary
```
User: Pavel
Chat: "Give me a summary of the entire move - what's done and what's pending?"
Expected: Agent provides comprehensive summary:
- All packing: DONE
- Move: COMPLETE
- All admin tasks: DONE
- Pending: Internet technician visit, some unpacking
- Issues: wardrobe scratch
- Total cost so far: 25000 (movers)
```

---

## Verification Queries

### Neo4j Checks
```cypher
// All inventory items
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'box' OR k.content CONTAINS 'inventory'
RETURN k.content;

// All tasks
MATCH (k:KnowledgeItem {projectId: '<project_id>', type: 'TASK'})
RETURN k.content, k.status;

// Timeline events
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'January'
RETURN k.content ORDER BY k.createdAt;
```

---

## Expected Data Summary

After successful test:
- 3 users registered
- 1 shared project
- Room inventories for 5 areas
- ~25 box labels tracked
- 11 tasks (all completed)
- Moving company details
- Timeline of events
- Issues logged

---

## Key Test Points

1. **Inventory management**: Track items by room/category
2. **Task dependencies**: Packing before moving
3. **Multi-user coordination**: Different people, different responsibilities
4. **Status tracking**: What's packed, moved, unpacked
5. **Issue logging**: Record problems during move
6. **Summary generation**: Comprehensive status reports

---

## Cleanup

```sql
DELETE FROM users WHERE email IN ('pavel@test.com', 'anya@test.com', 'vera@test.com');
```

```cypher
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
DETACH DELETE k;
```
