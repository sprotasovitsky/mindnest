# Test Scenario 006: Wedding Planning

## Overview

A couple (Nikita and Masha) with help from parents (Olga - Masha's mom) plan their wedding. They:
1. Manage guest list (100+ people)
2. Track venue, catering, entertainment bookings
3. Budget tracking
4. Task assignment to wedding party
5. Day-of timeline coordination

## Complexity: Medium (3 users, large data)

## Prerequisites

- Docker containers running (PostgreSQL, Neo4j, Qdrant)
- Backend running on http://localhost:8080
- Clean database (or isolated test data)

## Users

| Name   | Email            | Password |
|--------|-----------------|----------|
| Nikita | nikita@test.com | test123  |
| Masha  | masha@test.com  | test123  |
| Olga   | olga@test.com   | test123  |

## Test Execution

### Phase 1: Setup

#### Step 1.1: Register users
```
POST /api/auth/register
{ "email": "nikita@test.com", "password": "test123", "name": "Nikita" }
{ "email": "masha@test.com", "password": "test123", "name": "Masha" }
{ "email": "olga@test.com", "password": "test123", "name": "Olga" }
```

#### Step 1.2: Create project
```
User: Nikita
POST /api/projects { "name": "Wedding Nikita & Masha", "description": "Wedding planning for March 15, 2025" }
```

#### Step 1.3: Add team
```
User: Nikita
POST /api/projects/{projectId}/members { "email": "masha@test.com" }
POST /api/projects/{projectId}/members { "email": "olga@test.com" }
```

---

### Phase 2: Basic Info & Budget

#### Step 2.1: Wedding date and budget
```
User: Nikita
Chat: "Our wedding date is March 15, 2025. Total budget: 1,500,000 rubles. Key info:
- Venue ceremony: City Hall ZAGS at 2pm
- Venue reception: Restaurant 'Starry Night'
- Expected guests: 80-100 people
- Theme: Classic romantic, colors: white, gold, blush pink"
Expected: Agent saves key wedding details
```

#### Step 2.2: Budget breakdown
```
User: Masha
Chat: "Budget allocation:
- Venue & catering: 600,000 (40%)
- Photography/video: 150,000 (10%)
- Bride's dress & accessories: 150,000 (10%)
- Groom's suit: 50,000 (3%)
- Flowers & decor: 100,000 (7%)
- Music/DJ/band: 80,000 (5%)
- Wedding cake: 40,000 (3%)
- Rings: 100,000 (7%)
- Invitations & stationery: 30,000 (2%)
- Transportation: 50,000 (3%)
- Honeymoon: 100,000 (7%)
- Emergency fund: 50,000 (3%)"
Expected: Agent saves budget categories
```

---

### Phase 3: Guest List Management

#### Step 3.1: Groom's side
```
User: Nikita
Chat: "Adding guests from my side:
Family (15):
- Parents: Viktor and Elena Petrov - 2
- Sister Anna + husband Dmitry + son Misha - 3
- Grandparents: Nikolai and Maria - 2
- Uncle Sergey + wife + 2 kids - 4
- Aunt Natasha + husband - 2
- Cousin Igor + girlfriend - 2

Friends (20):
- Best man Alexey + wife - 2
- Groomsmen: Kirill, Maxim, Andrey - each with +1 = 6
- University friends: 8 people
- Work colleagues: 4 people

Total my side: 35 guests"
Expected: Agent saves guest list with categories
```

#### Step 3.2: Bride's side
```
User: Masha
Chat: "My guest list:
Family (18):
- Mom Olga + stepdad Pyotr - 2
- Dad Alexander + stepmom - 2
- Sister Yulia + husband + daughter - 3
- Grandma Zoya - 1
- Aunt Marina + husband + son + daughter - 4
- Aunt Svetlana + husband - 2
- Cousins: 4 people

Friends (25):
- Maid of honor Dasha - 1
- Bridesmaids: Liza, Nastya, Polina - each with +1 = 6
- School friends: 10 people
- Dance class friends: 8 people

Total my side: 43 guests"
Expected: Agent saves guest list
```

#### Step 3.3: Guest count check
```
User: Olga
Chat: "How many guests do we have total?"
Expected: Agent calculates: 35 + 43 = 78 guests
```

#### Step 3.4: Add more guests
```
User: Nikita
Chat: "Adding 12 more work colleagues - they're great people and I want them there"
Expected: Agent updates count to 90
```

#### Step 3.5: Guest dietary restrictions
```
User: Masha
Chat: "Note dietary restrictions:
- Grandma Zoya: diabetic, no sugar
- Cousin Igor's girlfriend: vegetarian
- Aunt Natasha: gluten-free
- My friend Liza: allergic to nuts
- 3 children need kids menu"
Expected: Agent saves dietary notes
```

---

### Phase 4: Vendor Bookings

#### Step 4.1: Venue booked
```
User: Olga
Chat: "Restaurant 'Starry Night' confirmed!
- Date: March 15, 2025, 4pm-midnight
- Capacity: 100 people
- Cost: 5500 per person = 495,000 for 90 people
- Menu: 5-course dinner + drinks package
- Deposit paid: 150,000 (30%)
- Balance due: 345,000 by March 1
Contact: Manager Anna, +7-999-555-1234"
Expected: Agent saves venue booking
```

#### Step 4.2: Photographer
```
User: Masha
Chat: "Booked photographer Viktor Smirnov:
- Full day coverage (10am-midnight)
- Second shooter included
- Engagement shoot included
- 500 edited photos + highlight video
- Cost: 120,000
- Deposit: 40,000 paid
Contact: +7-999-555-5678"
Expected: Agent saves booking
```

#### Step 4.3: Flowers
```
User: Masha
Chat: "Florist 'Bloom & Wild' booked:
- Bridal bouquet (roses, peonies)
- 4 bridesmaid bouquets
- 10 table centerpieces
- Ceremony arch flowers
- Boutonnieres for groomsmen
- Cost: 95,000
- Deposit: 30,000 paid"
Expected: Agent saves booking
```

#### Step 4.4: DJ
```
User: Nikita
Chat: "DJ Roma booked:
- 6pm-midnight
- Sound system included
- Will play both Russian and English music
- Special request: no Macarena!
- Cost: 60,000
- Deposit: 20,000 paid"
Expected: Agent saves booking
```

#### Step 4.5: Budget check
```
User: Olga
Chat: "How much have we spent so far vs budget?"
Expected: Agent calculates:
- Venue: 495,000 / 600,000 budget
- Photo: 120,000 / 150,000 budget
- Flowers: 95,000 / 100,000 budget
- DJ: 60,000 / 80,000 budget
Total committed: 770,000 / 1,500,000
Deposits paid: 240,000
```

---

### Phase 5: Task Assignment

#### Step 5.1: Create pre-wedding tasks
```
User: Masha
Chat: "Create tasks for the team:

For Masha (by Feb 15):
- Final dress fitting
- Choose bridesmaid dresses
- Book hair & makeup artist
- Order wedding cake

For Nikita (by Feb 15):
- Get suit fitted
- Organize bachelor party
- Book honeymoon flights
- Get wedding bands

For Olga (by Feb 20):
- Finalize seating chart
- Order invitations
- Coordinate with vendors
- Arrange transportation"
Expected: Agent creates 12 tasks
```

#### Step 5.2: Check task status
```
User: Nikita
Chat: "Show all tasks and who's responsible"
Expected: Agent lists all 12 tasks by person
```

---

### Phase 6: Task Completion

#### Step 6.1: Masha completes tasks
```
User: Masha
Chat: "Done with my tasks:
- Dress fitting done - perfect fit!
- Bridesmaid dresses: dusty rose, ordered
- Hair/makeup: Salon Elegance, 10am start
- Cake: 3-tier white with gold, 35,000 rubles
All complete!"
Expected: Agent marks 4 tasks done, records details
```

#### Step 6.2: Nikita completes tasks
```
User: Nikita
Chat: "My tasks done:
- Suit: navy blue 3-piece, Hugo Boss, 45,000 rubles
- Bachelor party: Feb 28, escape room + bar
- Honeymoon: Maldives, March 17-24, flights + hotel 98,000
- Rings: matching platinum bands, 95,000
Done!"
Expected: Agent marks 4 tasks done, records details
```

#### Step 6.3: Olga completes tasks
```
User: Olga
Chat: "All done:
- Seating chart finalized (will send photo later)
- Invitations sent: 60 printed, 30 digital
- All vendors confirmed for March 15
- Transportation: 2 Mercedes for wedding party, bus for guests
Tasks complete!"
Expected: Agent marks 4 tasks done
```

---

### Phase 7: Guest RSVP Tracking

#### Step 7.1: RSVPs coming in
```
User: Olga
Chat: "RSVP update - confirmed attending:
- All family from both sides: 33 people
- 15 friends confirmed so far
- 5 declined (travel conflicts)
Update guest count to 48 confirmed, 32 pending"
Expected: Agent updates RSVP status
```

#### Step 7.2: More RSVPs
```
User: Masha
Chat: "More RSVPs in:
- 20 more friends confirmed
- 8 more declined
- 4 still pending
Update: 68 confirmed, 4 pending, 13 declined"
Expected: Agent updates count
```

#### Step 7.3: Final count
```
User: Nikita
Chat: "Final RSVP: 72 guests attending. Update venue accordingly."
Expected: Agent records final count
```

---

### Phase 8: Wedding Day Timeline

#### Step 8.1: Create timeline
```
User: Masha
Chat: "Wedding day timeline:
8:00 - Bride hair & makeup starts
10:00 - Photographer arrives at bride's location
11:00 - Groom getting ready photos
12:30 - First look photoshoot
13:30 - Travel to ZAGS
14:00 - Ceremony at ZAGS
14:30 - Family photos outside ZAGS
15:00 - Travel to restaurant
15:30 - Cocktail hour begins
16:30 - Guests seated
17:00 - Grand entrance & first dance
17:30 - Dinner service begins
19:00 - Speeches
20:00 - Cake cutting
20:30 - Party & dancing
23:30 - Last dance
00:00 - Farewell"
Expected: Agent saves detailed timeline
```

#### Step 8.2: Timeline query
```
User: Nikita
Chat: "When does the photographer arrive?"
Expected: Agent answers: 10:00 AM at bride's location
```

---

### Phase 9: Final Budget Summary

#### Step 9.1: Total expenses
```
User: Olga
Chat: "Give me a complete budget summary with all expenses"
Expected: Agent calculates all recorded expenses:
- Venue: 495,000 (72 guests at 5500 + adjustments)
- Photography: 120,000
- Flowers: 95,000
- DJ: 60,000
- Dress: (from task - unknown exact)
- Suit: 45,000
- Rings: 95,000
- Cake: 35,000
- Honeymoon: 98,000
- Transportation: estimated
- Invitations: estimated
Total: ~1,100,000 estimated
Budget remaining: ~400,000
```

#### Step 9.2: Payment schedule
```
User: Nikita
Chat: "What payments do we still owe?"
Expected: Agent lists:
- Venue balance: 345,000 by March 1
- Photo balance: 80,000 by March 15
- Flower balance: 65,000 by March 10
- DJ balance: 40,000 on wedding day
- Other vendor balances
```

---

## Verification Queries

### Neo4j Checks
```cypher
// Guest list
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'guest' OR k.content CONTAINS 'attending'
RETURN k.content;

// Vendors
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'booked' OR k.content CONTAINS 'deposit'
RETURN k.content;

// Tasks
MATCH (k:KnowledgeItem {projectId: '<project_id>', type: 'TASK'})
RETURN k.content, k.status;

// Budget items
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'rubles' OR k.content CONTAINS 'cost'
RETURN k.content;
```

---

## Expected Data Summary

After successful test:
- 3 users
- 1 project
- 72+ guest records with dietary notes
- 5+ vendor bookings
- 12 tasks (all completed)
- Budget tracking entries
- Wedding day timeline
- RSVP tracking history

---

## Key Test Points

1. **Large guest list**: Handle 70+ individual guest records
2. **Categorization**: Guests by side, vendors by type
3. **RSVP tracking**: Update counts over time
4. **Budget math**: Track expenses vs allocations
5. **Timeline queries**: Answer specific time questions
6. **Multi-user updates**: Three people adding information

---

## Cleanup

```sql
DELETE FROM users WHERE email IN ('nikita@test.com', 'masha@test.com', 'olga@test.com');
```

```cypher
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
DETACH DELETE k;
```
