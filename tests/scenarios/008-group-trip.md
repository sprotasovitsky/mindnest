# Test Scenario 008: Group Trip to Georgia

## Overview

Five friends (Sasha, Dima, Oleg, Nastya, Ira) plan a 7-day trip to Georgia. They:
1. Plan route and activities
2. Book accommodations and transport
3. Track shared expenses
4. Vote on destinations and activities
5. Coordinate logistics for 5 people

## Complexity: Complex (5 users)

## Prerequisites

- Docker containers running (PostgreSQL, Neo4j, Qdrant)
- Backend running on http://localhost:8080
- Clean database (or isolated test data)

## Users

| Name   | Email            | Password | Role   |
|--------|-----------------|----------|--------|
| Sasha  | sasha@test.com  | test123  | owner  |
| Dima   | dima@test.com   | test123  | member |
| Oleg   | oleg@test.com   | test123  | member |
| Nastya | nastya@test.com | test123  | member |
| Ira    | ira@test.com    | test123  | member |

## Project

| Field       | Value                          |
|-------------|--------------------------------|
| Name        | Georgia Trip 2025              |

## Onboarding

```
Description: "Five friends planning a 7-day trip to Georgia. Need to plan route, book places, track shared expenses."
Answers: "1. Route planning, accommodation/transport bookings, expense tracking. 2. Five friends - Sasha, Dima, Oleg, Nastya, Ira. 3. Amazing trip with fair expense splitting."
Confirm: "Yes, save it."
```

## Test Execution

### Phase 1: Setup

#### Step 1.1: Register users
```
POST /api/auth/register
{ "email": "sasha@test.com", "password": "test123", "name": "Sasha" }
{ "email": "dima@test.com", "password": "test123", "name": "Dima" }
{ "email": "oleg@test.com", "password": "test123", "name": "Oleg" }
{ "email": "nastya@test.com", "password": "test123", "name": "Nastya" }
{ "email": "ira@test.com", "password": "test123", "name": "Ira" }
```

#### Step 1.2: Create project
```
User: Sasha
POST /api/projects { "name": "Georgia Trip 2025", "description": "Group trip February 15-22" }
```

#### Step 1.3: Add all friends
```
User: Sasha
POST /api/projects/{projectId}/members { "email": "dima@test.com" }
POST /api/projects/{projectId}/members { "email": "oleg@test.com" }
POST /api/projects/{projectId}/members { "email": "nastya@test.com" }
POST /api/projects/{projectId}/members { "email": "ira@test.com" }
```

---

### Phase 2: Initial Planning

#### Step 2.1: Trip overview
```
User: Sasha
Chat: "Georgia trip planning! Key info:
- Dates: February 15-22, 2025 (7 nights)
- Travelers: 5 people (Sasha, Dima, Oleg, Nastya, Ira)
- Budget target: 50,000 rubles per person
- Must-see: Tbilisi, Kazbegi, wine region
- Flight from: Moscow"
Expected: Agent saves trip basics
```

#### Step 2.2: Route suggestions
```
User: Dima
Chat: "Route options:
Option A - Classic:
Day 1-2: Tbilisi
Day 3: Mtskheta (day trip)
Day 4-5: Kazbegi
Day 6: Sighnaghi (wine)
Day 7: Tbilisi

Option B - Adventure:
Day 1-2: Tbilisi
Day 3-5: Kazbegi + Juta hiking
Day 6-7: Kakheti wine tour

Let's vote!"
Expected: Agent saves route options
```

#### Step 2.3: Voting
```
User: Oleg
Chat: "I vote Option A - more variety"
Expected: Agent records vote
```

```
User: Nastya
Chat: "Option A for me too - I want to see Sighnaghi"
Expected: Agent records vote
```

```
User: Ira
Chat: "Option B sounds more adventurous... but okay, A"
Expected: Agent records vote
```

```
User: Sasha
Chat: "Option A it is - 4 votes! Dima?"
Expected: Agent records vote count
```

```
User: Dima
Chat: "I wanted B but majority wins. Option A confirmed!"
Expected: Agent records final decision
```

---

### Phase 3: Flight Booking

#### Step 3.1: Flight search
```
User: Nastya
Chat: "Found flights Moscow-Tbilisi:
1. Aeroflot: 15,200 per person, depart 7:00, arrive 11:00
2. Georgian Airways: 13,800 per person, depart 10:30, arrive 14:30
3. S7: 14,500 per person, depart 14:00, arrive 18:00

Return Feb 22:
1. Aeroflot: 14,800, depart 12:00, arrive 14:00
2. Georgian Airways: 13,200, depart 15:30, arrive 17:30"
Expected: Agent saves flight options
```

#### Step 3.2: Flight decision
```
User: Sasha
Chat: "Let's take Georgian Airways both ways - best price and decent times. Total per person: 13,800 + 13,200 = 27,000 rubles for flights"
Expected: Agent records decision
```

#### Step 3.3: Booking confirmed
```
User: Nastya
Chat: "Flights booked for all 5 of us! Georgian Airways, confirmation: GEO2025FEB. Total paid: 135,000 rubles (27,000 x 5). I paid on my card, everyone owes me 27,000"
Expected: Agent records booking and debt
```

---

### Phase 4: Accommodation

#### Step 4.1: Tbilisi accommodation
```
User: Ira
Chat: "Tbilisi options (for 5 people):
1. Airbnb apartment in Old Town - 2BR, 8,000/night, great reviews
2. Fabrika Hostel - 5 beds in private room, 5,000/night
3. Hotel Rooms - 2 rooms at 6,000 each = 12,000/night

We need nights: Feb 15, 16, 21 (3 nights in Tbilisi)"
Expected: Agent saves options
```

#### Step 4.2: Tbilisi vote
```
User: Dima
Chat: "Airbnb! More comfortable for 5 of us"
Expected: Agent records vote
```

```
User: Oleg
Chat: "Agree, Airbnb"
Expected: Agent records vote
```

```
User: Sasha
Chat: "Airbnb works for me"
Expected: Agent records vote
```

```
User: Nastya
Chat: "Airbnb unanimous. 8,000 x 3 nights = 24,000 for Tbilisi"
Expected: Agent records decision
```

#### Step 4.3: Kazbegi accommodation
```
User: Ira
Chat: "Kazbegi options (2 nights: Feb 17-18):
1. Rooms Hotel Kazbegi - stunning views, 15,000/night for 2 rooms
2. Guesthouse - 6,000/night, 2 rooms
3. Hostel in Stepantsminda - 3,500/night

Rooms Hotel is amazing but pricey..."
Expected: Agent saves options
```

#### Step 4.4: Kazbegi discussion
```
User: Oleg
Chat: "Rooms Hotel is once in a lifetime views. I say splurge!"
Expected: Agent records opinion
```

```
User: Nastya
Chat: "Too expensive. Guesthouse is fine"
Expected: Agent records opinion
```

```
User: Dima
Chat: "Compromise - Rooms Hotel for 1 night, guesthouse for 1 night?"
Expected: Agent records suggestion
```

```
User: Sasha
Chat: "Great idea Dima! Night 1 at Rooms Hotel (15,000), Night 2 at guesthouse (6,000). Total: 21,000 for Kazbegi"
Expected: Agent records decision
```

#### Step 4.5: Sighnaghi accommodation
```
User: Ira
Chat: "Sighnaghi for Feb 19-20 (2 nights):
Booked cozy guesthouse with wine cellar access - 7,000/night x 2 = 14,000"
Expected: Agent records booking
```

#### Step 4.6: Total accommodation
```
User: Sasha
Chat: "Total accommodation cost?"
Expected: Agent calculates:
- Tbilisi: 24,000
- Kazbegi: 21,000
- Sighnaghi: 14,000
Total: 59,000 rubles (11,800 per person)
```

---

### Phase 5: Activities Planning

#### Step 5.1: Tbilisi activities
```
User: Dima
Chat: "Tbilisi must-do list:
- Old Town walking tour (free)
- Sulfur baths - 50 lari (~1,700 rub) for private room
- Cable car to Narikala - 5 lari (~170 rub)
- Food tour - 100 lari (~3,400 rub) per person
- Dry Bridge flea market (free)
- Wine tasting at 8000 Vintages - 80 lari (~2,700 rub) per person"
Expected: Agent saves activity list
```

#### Step 5.2: Kazbegi activities
```
User: Oleg
Chat: "Kazbegi plan:
- Hire jeep to Gergeti Trinity Church - 150 lari (~5,100 rub) for 5 people
- Hiking to Gveleti waterfall (free, 3 hours)
- Sunrise at Rooms Hotel terrace (just wake up early!)
- Optional: paragliding 250 lari (~8,500 rub) per person - anyone interested?"
Expected: Agent saves activities
```

#### Step 5.3: Paragliding vote
```
User: Oleg
Chat: "Who's in for paragliding?"
Expected: Agent starts vote
```

```
User: Sasha
Chat: "I'm in!"
Expected: Agent records yes
```

```
User: Dima
Chat: "Yes! Always wanted to try"
Expected: Agent records yes
```

```
User: Nastya
Chat: "Too scary for me, pass"
Expected: Agent records no
```

```
User: Ira
Chat: "I'll watch you guys from below 😄"
Expected: Agent records no
```

```
User: Oleg
Chat: "3 people for paragliding: Oleg, Sasha, Dima. Cost: 8,500 x 3 = 25,500 (not shared with girls)"
Expected: Agent records decision and cost allocation
```

#### Step 5.4: Wine tour
```
User: Nastya
Chat: "Kakheti wine tour from Sighnaghi:
- Full day with driver: 200 lari (~6,800 rub) for the group
- Includes: 3 wineries, lunch, qvevri wine tasting
- Kindzmarauli, Tsinandali, Mukuzani tastings
Booking for Feb 20"
Expected: Agent saves activity
```

---

### Phase 6: Transportation

#### Step 6.1: Getting around
```
User: Dima
Chat: "Transport planning:
- Airport transfer: taxi ~100 lari (~3,400 rub) each way
- Tbilisi-Kazbegi: marshrutka 25 lari/person or private car 250 lari total
- Kazbegi-Sighnaghi: need to figure out
- Sighnaghi-Tbilisi: marshrutka 15 lari/person

I suggest private car Tbilisi-Kazbegi for comfort"
Expected: Agent saves transport options
```

#### Step 6.2: Car rental option
```
User: Oleg
Chat: "Alternative: rent a car for the whole trip?
SUV rental: 200 lari/day x 7 days = 1,400 lari (~47,600 rub)
+ fuel estimate: 200 lari (~6,800 rub)
Total: ~54,400 rub = 10,880 per person

Pros: flexibility, can stop anywhere
Cons: need confident mountain driver"
Expected: Agent saves option
```

#### Step 6.3: Driver vote
```
User: Sasha
Chat: "I can drive mountain roads. Who votes for rental car?"
Expected: Agent starts vote
```

```
User: Dima
Chat: "Car rental yes! More freedom"
Expected: Agent records vote
```

```
User: Oleg
Chat: "Yes to car"
Expected: Agent records vote
```

```
User: Nastya
Chat: "Car sounds good"
Expected: Agent records vote
```

```
User: Ira
Chat: "Sure, as long as Sasha drives the mountain parts!"
Expected: Agent records vote
```

```
User: Sasha
Chat: "Unanimous! Renting SUV. I'll book through LocalRent.ge. Will add airport pickup."
Expected: Agent records decision
```

---

### Phase 7: Budget Tracking

#### Step 7.1: Pre-trip expenses
```
User: Sasha
Chat: "Let's track who paid what so far:
- Nastya: flights 135,000
- Ira: Tbilisi Airbnb 24,000
- Sasha: Car rental 54,400
Who's booking remaining accommodations?"
Expected: Agent records payments
```

#### Step 7.2: More bookings
```
User: Oleg
Chat: "I booked:
- Rooms Hotel Kazbegi: 15,000
- Kazbegi guesthouse: 6,000
Total: 21,000 paid by me"
Expected: Agent records payment
```

```
User: Dima
Chat: "I booked Sighnaghi guesthouse: 14,000 paid"
Expected: Agent records payment
```

#### Step 7.3: Pre-trip summary
```
User: Nastya
Chat: "What's our total pre-booked expenses and who owes whom?"
Expected: Agent calculates:
Total pre-booked: 248,400
Per person share: 49,680

Paid:
- Nastya: 135,000 (owes: -85,320 = receives 85,320)
- Ira: 24,000 (owes: 25,680)
- Sasha: 54,400 (owes: -4,720 = receives 4,720)
- Oleg: 21,000 (owes: 28,680)
- Dima: 14,000 (owes: 35,680)
```

---

### Phase 8: Trip Execution (Daily Log)

#### Step 8.1: Day 1 - Arrival
```
User: Sasha
Chat: "Feb 15: Arrived in Tbilisi! Got the car, drove to apartment. Evening expenses:
- Dinner at Shavi Lomi: 250 lari (~8,500 rub) for 5 = 1,700 each
- Wine at dinner: 80 lari
- Paid by: Sasha"
Expected: Agent logs day and expenses
```

#### Step 8.2: Day 2 - Tbilisi
```
User: Nastya
Chat: "Feb 16 expenses:
- Breakfast at Stamba: 120 lari (Nastya paid)
- Sulfur baths: 50 lari (Dima paid)
- Cable car: 25 lari total (Ira paid)
- Lunch at Cafe Littera: 180 lari (Oleg paid)
- Wine tasting 8000 Vintages: 400 lari for 5 (Sasha paid)
Amazing day!"
Expected: Agent logs expenses with payers
```

#### Step 8.3: Day 3 - Drive to Kazbegi
```
User: Dima
Chat: "Feb 17: Road trip day! Expenses:
- Gas fill: 100 lari (Sasha)
- Lunch on the way: 90 lari (Nastya)
- Rooms Hotel check-in: already paid
- Dinner at hotel: 300 lari (Dima)
Views from the room are INSANE"
Expected: Agent logs expenses
```

#### Step 8.4: Day 4 - Kazbegi Adventures
```
User: Oleg
Chat: "Feb 18: Epic day!
- Jeep to Gergeti Church: 150 lari (Oleg)
- Paragliding for 3: 750 lari (split between Oleg, Sasha, Dima - 250 each)
- Guesthouse check-in: already paid
- Dinner: 150 lari (Ira)
Paragliding was AMAZING!"
Expected: Agent logs, notes paragliding split differently
```

#### Step 8.5: Day 5 - To Sighnaghi
```
User: Ira
Chat: "Feb 19: Drive to wine country
- Gas: 80 lari (Sasha)
- Lunch stop: 100 lari (Nastya)
- Guesthouse dinner included
- Evening wine from cellar: 60 lari (Dima)
Sighnaghi is so charming!"
Expected: Agent logs expenses
```

#### Step 8.6: Day 6 - Wine Tour
```
User: Nastya
Chat: "Feb 20: Wine tour day!
- Wine tour with driver: 200 lari (Oleg)
- Extra wine purchases:
  * Oleg: 150 lari
  * Nastya: 100 lari
  * Sasha: 80 lari
  * Dima: 120 lari
  * Ira: 90 lari
Best day ever! So much wine 🍷"
Expected: Agent logs expenses (personal wine not shared)
```

#### Step 8.7: Day 7 - Back to Tbilisi
```
User: Sasha
Chat: "Feb 21: Last full day
- Gas: 60 lari (Sasha)
- Dry Bridge market purchases (personal)
- Final dinner at Barbarestan: 450 lari (Nastya)
- Wine bar after: 200 lari (Dima)
Tomorrow we fly home 😢"
Expected: Agent logs expenses
```

#### Step 8.8: Day 8 - Departure
```
User: Dima
Chat: "Feb 22: Departure day
- Breakfast: 80 lari (Ira)
- Car drop-off (no extra charges!)
- Airport - flight on time
Georgia was incredible!"
Expected: Agent logs final expenses
```

---

### Phase 9: Final Settlement

#### Step 9.1: Trip expense summary
```
User: Sasha
Chat: "Calculate all trip expenses and who owes whom"
Expected: Agent calculates comprehensive breakdown:

Pre-trip (per person share 49,680):
- Individual payments tracked

During trip shared expenses (lari converted):
- Day 1-8 shared meals, transport, activities

Personal (not shared):
- Paragliding (3 people only)
- Wine purchases (individual)

Final settlement showing who pays whom
```

#### Step 9.2: Total per person
```
User: Nastya
Chat: "What did the trip cost each of us total?"
Expected: Agent calculates approximately:
- Flights: 27,000
- Accommodation share: 11,800
- Car share: 10,880
- Food/activities share: ~15,000
- Personal purchases: varies
Total ~65,000-70,000 per person
```

#### Step 9.3: Debt settlement
```
User: Oleg
Chat: "Simplify the debts - who needs to pay whom and how much?"
Expected: Agent calculates optimal settlement (minimize transactions)
```

---

### Phase 10: Trip Memories

#### Step 10.1: Best moments
```
User: Ira
Chat: "Save our top trip moments:
1. Sunrise at Rooms Hotel with mountains
2. Paragliding over Kazbegi (for those who did it)
3. Wine cellar dinner in Sighnaghi
4. Getting lost in Tbilisi old town
5. Georgian hospitality everywhere"
Expected: Agent saves memories
```

#### Step 10.2: Recommendations
```
User: Dima
Chat: "Save restaurant recommendations for friends:
- Shavi Lomi (Tbilisi) - best khinkali
- Cafe Littera (Tbilisi) - upscale Georgian
- Rooms Hotel restaurant (Kazbegi) - views + food
- Any random village supra - most authentic"
Expected: Agent saves recommendations
```

#### Step 10.3: Trip rating
```
User: Sasha
Chat: "Trip rating from everyone?"
Expected: Agent prompts ratings
```

```
User: Sasha
Chat: "10/10 would do again!"
```

```
User: Dima
Chat: "10/10 - best trip ever"
```

```
User: Oleg
Chat: "9/10 - wanted more hiking"
```

```
User: Nastya
Chat: "10/10 - the wine! 🍷"
```

```
User: Ira
Chat: "10/10 - amazing company and country"
Expected: Agent records all ratings, average: 9.8/10
```

---

## Verification Queries

### Neo4j Checks
```cypher
// All bookings
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'booked' OR k.content CONTAINS 'paid'
RETURN k.content, k.ownerId;

// Daily logs
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'Feb'
RETURN k.content ORDER BY k.createdAt;

// Votes and decisions
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'vote' OR k.content CONTAINS 'unanimous'
RETURN k.content;

// Expenses
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'lari' OR k.content CONTAINS 'rub'
RETURN k.content;
```

---

## Expected Data Summary

After successful test:
- 5 users
- 1 project
- Trip itinerary (7 days)
- Multiple voting records
- Flight, hotel, car bookings
- Daily expense logs
- Complex debt tracking (shared vs personal)
- Settlement calculations
- Trip memories and recommendations

---

## Key Test Points

1. **Multi-user voting**: 5 people vote on various decisions
2. **Complex expense splitting**: Some shared, some partial (paragliding), some personal
3. **Multi-currency**: Track in lari, convert to rubles
4. **Daily logging**: Chronological expense tracking
5. **Debt optimization**: Simplify who pays whom
6. **Itinerary changes**: Adapt plans based on votes

---

## Cleanup

```sql
DELETE FROM users WHERE email IN ('sasha@test.com', 'dima@test.com', 'oleg@test.com', 'nastya@test.com', 'ira@test.com');
```

```cypher
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
DETACH DELETE k;
```
