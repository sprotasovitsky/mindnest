# Test Scenario 004: Book Club

## Overview

Two friends (Lena and Katya) run a book club. They:
1. Track books they've read
2. Save favorite quotes and thoughts
3. Rate and review books
4. Decide what to read next
5. Schedule discussion meetings

## Complexity: Simple (2 users)

## Prerequisites

- Docker containers running (PostgreSQL, Neo4j, Qdrant)
- Backend running on http://localhost:8080
- Clean database (or isolated test data)

## Users

| Name  | Email           | Password |
|-------|----------------|----------|
| Lena  | lena@test.com  | test123  |
| Katya | katya@test.com | test123  |

## Test Execution

### Phase 1: Setup

#### Step 1.1: Register users
```
POST /api/auth/register
{ "email": "lena@test.com", "password": "test123", "name": "Lena" }
{ "email": "katya@test.com", "password": "test123", "name": "Katya" }
```

#### Step 1.2: Lena creates the project
```
User: Lena
POST /api/projects { "name": "Our Book Club 2025", "description": "Reading together" }
```

#### Step 1.3: Add Katya to project
```
User: Lena
POST /api/projects/{projectId}/members { "email": "katya@test.com" }
```

---

### Phase 2: Adding Past Books

#### Step 2.1: Lena adds first book
```
User: Lena
Chat: "Let's start tracking our book club! Our first book was 'The Master and Margarita' by Mikhail Bulgakov. We read it in October. I give it 5 stars - absolute masterpiece!"
Expected: Agent saves book with rating and date
```

#### Step 2.2: Katya adds her rating
```
User: Katya
Chat: "I also loved Master and Margarita! 5 stars from me too. My favorite quote: 'Manuscripts don't burn.'"
Expected: Agent adds rating and quote
```

#### Step 2.3: Lena adds a quote
```
User: Lena
Chat: "Adding my favorite quote from the book: 'Cowardice is the most terrible of vices.'"
Expected: Agent saves quote linked to book
```

#### Step 2.4: Second book
```
User: Lena
Chat: "In November we read '1984' by George Orwell. I rate it 4 stars - important but depressing."
Expected: Agent saves book entry
```

#### Step 2.5: Katya's thoughts on 1984
```
User: Katya
Chat: "1984 was heavy but necessary. 4 stars. Quote to remember: 'War is peace. Freedom is slavery. Ignorance is strength.'"
Expected: Agent adds rating and quote
```

---

### Phase 3: Current Book Discussion

#### Step 3.1: Starting new book
```
User: Lena
Chat: "We're starting 'Crime and Punishment' by Dostoevsky for December. It's 600 pages, so let's plan to finish by December 28."
Expected: Agent creates current book with deadline
```

#### Step 3.2: Reading progress
```
User: Katya
Chat: "I'm on page 150 of Crime and Punishment. Raskolnikov is such a complex character!"
Expected: Agent records progress and thought
```

#### Step 3.3: Lena's progress
```
User: Lena
Chat: "Page 200 here. Adding thought: the psychological tension is incredible. Dostoevsky really gets inside the mind of guilt."
Expected: Agent records progress and thought
```

#### Step 3.4: Katya adds quote
```
User: Katya
Chat: "Great quote from page 180: 'Pain and suffering are always inevitable for a large intelligence and a deep heart.'"
Expected: Agent saves quote with page number
```

#### Step 3.5: Check progress
```
User: Lena
Chat: "How far are we both in the current book?"
Expected: Agent shows:
- Lena: page 200
- Katya: page 150
- Book total: 600 pages
```

---

### Phase 4: Book Completion & Review

#### Step 4.1: Katya finishes
```
User: Katya
Chat: "Finished Crime and Punishment! What a journey. Rating: 5 stars. The ending with redemption through love was beautiful."
Expected: Agent records completion and rating
```

#### Step 4.2: Lena finishes
```
User: Lena
Chat: "Done! 5 stars from me too. Final thought: this book changed how I think about morality and redemption."
Expected: Agent records completion and rating
```

#### Step 4.3: Average rating
```
User: Katya
Chat: "What's the average rating for Crime and Punishment?"
Expected: Agent calculates: (5 + 5) / 2 = 5 stars
```

---

### Phase 5: Deciding Next Book

#### Step 5.1: Suggestions
```
User: Lena
Chat: "For January, I suggest either 'Anna Karenina' by Tolstoy or 'The Brothers Karamazov' by Dostoevsky. What do you think?"
Expected: Agent saves suggestions
```

#### Step 5.2: Katya's preference
```
User: Katya
Chat: "I vote for Anna Karenina - I want something different from Dostoevsky. Also suggesting 'War and Peace' as third option."
Expected: Agent records vote and adds suggestion
```

#### Step 5.3: Decision
```
User: Lena
Chat: "Let's go with Anna Karenina! It's our January book. About 800 pages, deadline January 31."
Expected: Agent creates new book entry with deadline
```

---

### Phase 6: Book Club Statistics

#### Step 6.1: Books read
```
User: Katya
Chat: "How many books have we read together?"
Expected: Agent answers: 3 books (Master and Margarita, 1984, Crime and Punishment)
```

#### Step 6.2: All quotes
```
User: Lena
Chat: "Show me all the quotes we've saved"
Expected: Agent lists all saved quotes with book attribution
```

#### Step 6.3: Highest rated
```
User: Katya
Chat: "Which book had the highest rating?"
Expected: Agent answers: Master and Margarita and Crime and Punishment - both 5 stars
```

#### Step 6.4: Reading history
```
User: Lena
Chat: "What's our reading history with ratings?"
Expected: Agent lists:
- October: Master and Margarita - 5 stars
- November: 1984 - 4 stars
- December: Crime and Punishment - 5 stars
- January (current): Anna Karenina - in progress
```

---

### Phase 7: Meeting Planning

#### Step 7.1: Schedule meeting
```
User: Lena
Chat: "Let's schedule our book discussion meeting for January 31st at 7pm at my place"
Expected: Agent creates meeting/task
```

#### Step 7.2: Katya confirms
```
User: Katya
Chat: "January 31st works for me! Adding to my calendar. I'll bring wine."
Expected: Agent records confirmation and note
```

#### Step 7.3: Discussion questions
```
User: Lena
Chat: "Save these discussion questions for Anna Karenina:
1. Is Anna a victim of society or her own choices?
2. How does Tolstoy portray marriage?
3. What role does the train symbolism play?
4. Compare Levin and Vronsky as characters"
Expected: Agent saves discussion questions
```

---

## Verification Queries

### Neo4j Checks
```cypher
// All books
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'book' OR k.content CONTAINS 'stars'
RETURN k.content, k.ownerId;

// All quotes
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'quote' OR k.content CONTAINS '"'
RETURN k.content;

// Reading progress
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
WHERE k.content CONTAINS 'page'
RETURN k.content;
```

---

## Expected Data Summary

After successful test:
- 2 users registered
- 1 shared project
- 4 book entries (3 completed, 1 in progress)
- 4+ quote entries
- Reading progress records
- Discussion questions saved
- Meeting scheduled

---

## Key Test Points

1. **Multi-user ratings**: Both users rate same book, calculate average
2. **Quote storage**: Save quotes with attribution to books
3. **Progress tracking**: Track reading progress per user
4. **Decision making**: Record voting/decisions
5. **Historical queries**: Answer questions about past activities
6. **Planning**: Schedule future events

---

## Cleanup

```sql
DELETE FROM users WHERE email IN ('lena@test.com', 'katya@test.com');
```

```cypher
MATCH (k:KnowledgeItem {projectId: '<project_id>'})
DETACH DELETE k;
```
