# API Specification

## Base URL

```
http://localhost:8000
```

## Authentication

Most endpoints require JWT authentication. Include token in header:

```
Authorization: Bearer <token>
```

## CV Builder API

### Generate CV

**POST** `/api/cv/generate`

Generate a professional CV with AI enhancements.

**Request Body (multipart/form-data):**
- `user_id` (int, required): User ID
- `personal_info` (string, JSON): Personal information
- `experience` (string, JSON array): Work experience
- `education` (string, JSON array): Education history
- `skills` (string, JSON object): Skills (Europass format)
- `awards` (string, JSON array, optional): Awards
- `publications` (string, JSON array, optional): Publications
- `projects` (string, JSON array, optional): Projects
- `memberships` (string, JSON array, optional): Memberships
- `job_id` (int, optional): Job ID to tailor CV
- `photo` (file, optional): Profile photo

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "json_content": {...},
  "ai_score": 85.5,
  "photo_url": "/static/uploads/photo.jpg",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### Get CV

**GET** `/api/cv/{user_id}`

Get the latest CV for a user.

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "json_content": {...},
  "ai_score": 85.5,
  "photo_url": "/static/uploads/photo.jpg"
}
```

### Get CV Suggestions

**POST** `/api/cv/suggestions`

Get AI-powered suggestions for improving CV content.

**Request Body:**
```json
{
  "section": "experience",
  "content": "Worked on software development",
  "industry": "Technology"
}
```

**Response:**
```json
{
  "improvements": [
    {
      "weak": "worked on",
      "strong": "Executed and delivered",
      "context": "Replace 'worked on' with 'Executed and delivered' for more impact"
    }
  ],
  "recommendations": [
    "Add numbers or percentages to quantify achievements"
  ],
  "examples": [...]
}
```

### Calculate ATS Score

**POST** `/api/cv/ats-score`

Calculate ATS compatibility score.

**Request Body:**
```json
{
  "personal_info": {...},
  "summary": "...",
  "work_experience": [...],
  "education": [...],
  "personal_skills": {...}
}
```

**Response:**
```json
{
  "score": 85.0,
  "keyword_density": 2.5,
  "section_completeness": {
    "summary": true,
    "experience": true,
    "education": true,
    "skills": true
  },
  "formatting_score": 90.0,
  "recommendations": [...]
}
```

## Job Matching API

### Search Global Jobs

**GET** `/api/jobs/search-global`

Search global job market across multiple APIs.

**Query Parameters:**
- `query` (string, required): Job search query
- `location` (string, optional): Location filter
- `limit` (int, optional, default: 20): Maximum results

**Response:**
```json
{
  "jobs": [
    {
      "id": "job_123",
      "title": "Software Engineer",
      "company": "Tech Corp",
      "location": "Remote",
      "description": "...",
      "salary": "$50,000 - $80,000",
      "source": "linkedin",
      "url": "https://...",
      "posted_date": "2024-01-01"
    }
  ],
  "count": 10
}
```

### Match Jobs

**POST** `/api/jobs/match`

Match user to relevant job opportunities.

**Request Body:**
```json
{
  "user_id": 1,
  "limit": 10,
  "category": "Technology",
  "location": "Remote"
}
```

**Response:**
```json
{
  "matches": [
    {
      "job_id": 1,
      "job_title": "Software Engineer",
      "startup_name": "Tech Startup",
      "location": "Remote",
      "match_score": 0.85,
      "skills_match": 0.9,
      "degree_match": 1.0,
      "experience_match": 0.8
    }
  ],
  "count": 10
}
```

### Match Global Jobs

**POST** `/api/jobs/match-global`

Match user CV to global job opportunities.

**Request Body:**
```json
{
  "user_id": 1,
  "query": "software engineer",
  "location": "Remote",
  "limit": 20
}
```

**Response:**
```json
{
  "matches": [
    {
      "id": "job_123",
      "title": "Software Engineer",
      "company": "Tech Corp",
      "location": "Remote",
      "match_score": 0.75
    }
  ],
  "count": 15
}
```

## Investment Platform API

### List Startups

**GET** `/api/startups/list`

List verified startups available for investment.

**Query Parameters:**
- `skip` (int, optional, default: 0): Pagination offset
- `limit` (int, optional, default: 100): Results limit
- `sector` (string, optional): Filter by sector
- `min_credibility` (float, optional, default: 0.0): Minimum credibility score

**Response:**
```json
{
  "startups": [
    {
      "id": 1,
      "startup_id": "startup_123",
      "name": "Tech Startup",
      "sector": "Technology",
      "credibility_score": 85.5,
      "funding_goal": 100000,
      "verified": true,
      "on_chain": true
    }
  ],
  "count": 10
}
```

### Verify Startup

**GET** `/api/startups/verify/{startup_id}`

Verify a startup on the blockchain.

**Response:**
```json
{
  "startup_id": "startup_123",
  "verified": true,
  "on_chain": true,
  "credibility_score": 85.5,
  "transaction_signature": "5j7s8...",
  "blockchain_proof": {...}
}
```

### Get Startup Details

**GET** `/api/startups/{startup_id}`

Get detailed startup information.

**Response:**
```json
{
  "id": 1,
  "startup_id": "startup_123",
  "name": "Tech Startup",
  "sector": "Technology",
  "description": "...",
  "funding_goal": 100000,
  "credibility_score": 85.5,
  "founder": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com"
  },
  "verified": true,
  "on_chain": true,
  "blockchain_proof": {...}
}
```

### Send USDC Investment

**POST** `/api/investments/usdc/send`

Send USDC investment to a startup.

**Request Body:**
```json
{
  "investor_id": 1,
  "startup_id": "startup_123",
  "amount_usdc": 1000.0
}
```

**Response:**
```json
{
  "investment_id": "inv_123",
  "transaction_signature": "5j7s8...",
  "confirmation_url": "https://explorer.solana.com/tx/...",
  "blockchain_proof": {...},
  "amount_usdc": 1000.0,
  "timestamp": "2024-01-01T00:00:00"
}
```

### Get Portfolio

**GET** `/api/investments/portfolio/{investor_id}`

Get investor portfolio with all investments.

**Response:**
```json
{
  "investor_id": 1,
  "investor_name": "John Doe",
  "wallet_address": "5j7s8...",
  "total_invested_usdc": 5000.0,
  "total_investments": 3,
  "startup_count": 2,
  "startups": [
    {
      "startup_id": "startup_123",
      "startup_name": "Tech Startup",
      "total_invested": 3000.0,
      "investment_count": 2
    }
  ],
  "all_investments": [...]
}
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message"
}
```

**Status Codes:**
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `500`: Internal Server Error

