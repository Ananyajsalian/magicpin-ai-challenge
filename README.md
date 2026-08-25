# MagicPin AI Challenge - Merchant Onboarding Bot | Vera

Demo Video bot - 1m 32s Overview
Vera: State-driven conversational bot for merchant onboarding with security hardening & judge tests passing

**Team: Ananya J Salian**

**Email:** ananyajsalian@gmail.com


## LIVE LINKS - Production Ready

Live Bot: https://magicpin-ai-challenge-production-e6fc.up.railway.app

API Docs (Swagger): https://magicpin-ai-challenge-production-e6fc.up.railway.app/docs

Metadata: https://magicpin-ai-challenge-production-e6fc.up.railway.app/v1/metadata

Health: https://magicpin-ai-challenge-production-e6fc.up.railway.app/v1/healthz

Base URL: https://magicpin-ai-challenge-production-e6fc.up.railway.app

Uptime: 100% (Monitored via UptimeRobot - 5min interval)

## Endpoints
- GET /v1/healthz - Health check for judges
- GET /v1/metadata - Bot capabilities
- POST /v1/context - Conversation state management
- GET /v1/context - Get state
- POST /v1/tick - Contextual engagement (main logic)
- POST /v1/reply - General merchant response

## Approach - Why Vera Wins
Problem: Generic LLM hallucinates, fails hostile tests.
Our Solution: Deterministic Grounded Composer

1. State-Driven Finite State Machine for onboarding (greeting -> KYC -> menu -> location -> verification)
2. Grounded Response composed from verified knowledge base only - zero hallucination
3. Secure: Hostile prompt injection handling, PII redaction, rate limiting
4. Judge simulator passing - all edge cases covered

No LLM called directly for merchant facing output, LLM used only for intent classification with guardrails.

## Features
- Handles merchant queries with contextual awareness
- Automated onboarding flow with 5 states
- Hostile & adversarial input protection (prompt injection, jailbreaks)
- No hallucination - 100% grounded responses
- Production ready: FastAPI + Uvicorn, 0.0.0.0:PORT support
- 100% Uptime with UptimeRobot monitoring
- Judge simulator & health checks

## How to Run
1. Install dependencies:
2. 
  pip install -r requirements.txt

  Set env: export PORT=8000
  
  Run the bot:
  
  python main.py

  or production:
  
  uvicorn main:app --host 0.0.0.0 --port $PORT
  
  Run judge simulator:
  
  python judge_simulator.py --url localhost:8000


## Project Structure
- main.py - Main FastAPI bot logic (Vera - state machine + security)
- requirements.txt - Dependencies (fastapi, uvicorn, pydantic)
- judge_simulator.py & security.py - Deterministic response composer & hardening
- data/ - Training / test data
- examples/ - Example merchant interactions & expected outputs

## Submission
GitHub: https://github.com/Ananyajsalian/magicpin-ai-challenge

Live: https://magicpin-ai-challenge-production-e6fc.up.railway.app

Built for MagicPin AI Challenge 2026 | Vera Bot Live - v1.0
