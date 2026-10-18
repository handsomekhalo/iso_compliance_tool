# RandRail - ISO 20022 Compliance Platform


# RandRail

Lightweight ISO 20022 message quality scoring, legacy file normalisation, and audit archive.

Built for organisations that still run older payment systems and need a practical way to check message quality, keep evidence, and produce clean reports — without replacing their core systems.

## What it does

RandRail sits beside existing systems and helps with two related problems:

### 1. Audit & Evidence Archive
- Upload original payment files (ISO 20022 XML or common legacy formats)
- Automatic cryptographic hash (SHA-256) of every file
- Compliance / quality score based on configurable rules
- Full record of who uploaded what and when
- Exportable CSV and branded PDF reports for internal audit or regulators
- Files stored in cloud object storage (Backblaze B2)

### 2. Legacy File Normaliser + Scorer
- Accepts XML, CSV, Excel and JSON files that still circulate in older environments
- Maps available fields and scores completeness against a configurable rule set
- Produces structured results and clear issue lists
- Helps teams see gaps before files move further downstream

## Who it is for

- Mid-size remittance and payment companies
- Smaller or regional financial institutions still running legacy cores
- Corporate treasury and finance teams handling mixed payment files
- Ops and compliance teams that need clean audit evidence without a heavy enterprise suite

It is **not** a full SWIFT gateway, MT↔MX translator, or core banking replacement.

## Current status (dev branch)

**Working**
- Multi-tenant bank accounts with API keys
- Role-based access (end user → institution admin → super admin)
- ISO 20022 XML parsing with auto message-type detection
- Dynamic field rules stored in the database (weights configurable)
- Quality / compliance scoring engine
- File upload → parse → score → hash → cloud storage pipeline
- Reconciliation log list & detail APIs
- CSV + PDF export
- Basic support for CSV / Excel / JSON intake

**In progress / planned**
- Stronger content validation (lengths, regex, basic format checks)
- Clearer mapping layer for legacy formats
- Automated test suite with real sample files
- Production UI polish and full user-management screens
- Security hardening for production use

## Tech stack

- Backend: Django + Django REST Framework, PostgreSQL
- Frontend: Next.js (React)
- Storage: Backblaze B2
- Auth: Token-based, bank-scoped permissions
- Deployment: Railway (API) + Vercel (frontend)

## Live demo

- Frontend: https://iso-compliance-tool.vercel.app
- Backend API: https://isocompliancetool-production.up.railway.app

## Important notes

- The “XRPL audit hash” currently stores a SHA-256 hash of the file content. It is a cryptographic audit trail, not a live write to the XRP Ledger.
- Scoring is driven by configurable rules. Depth of validation is being improved; treat current scores as a useful first-pass quality signal.
- Lightning / remittance features exist in the codebase but are separate from the core archive + scoring product and remain in mock mode.

## Regulatory context

The platform is designed with South African requirements in mind (POPIA, record-keeping, auditability).  
Sandbox / regulatory engagement is a separate workstream.

## Author

Titus Monaheng  
[LinkedIn](http://www.linkedin.com/in/khalo-monaheng-b6a821b0)

---

Built as a practical tool for teams that still live with older payment files and need better visibility, scoring, and evidence — not as a replacement for enterprise payments platforms.

<!-- A production-grade fintech platform for ISO 20022 payment reconciliation, 
built for South African banks facing the November 2025 SWIFT migration deadline.

## 🚀 Live Demo
- **Frontend**: https://iso-compliance-tool.vercel.app
- **Backend API**: https://isocompliancetool-production.up.railway.app

## 🏗️ Architecture
- **Backend**: Django REST Framework + PostgreSQL
- **Frontend**: Next.js (React)
- **Storage**: Backblaze B2 (S3-compatible)
- **Blockchain**: XRP Ledger (audit hashing)
- **Deployment**: Railway (backend) + Vercel (frontend)

## ✨ Features
- ISO 20022 XML message parsing (pain.001, camt.053)
- Real-time reconciliation with 95%+ accuracy
- Blockchain audit trail generation
- Cloud-based document storage
- Transaction analytics dashboard

## 🔧 Tech Stack
**Backend**: Python, Django, Django REST Framework, PostgreSQL, psycopg2  
**Frontend**: Next.js, React, Axios, TailwindCSS  
**Cloud**: Railway, Vercel, Backblaze B2  
**Blockchain**: XRP Ledger  
**Tools**: Git, GitHub, Postman

## 📜 Regulatory Compliance
Applied for SARB IFWG Regulatory Sandbox approval.  
Compliant with: FAIS Act, NPS Act, FIC Act, POPIA

## 👨‍💻 Author
Titus Monaheng - [LinkedIn](http://www.linkedin.com/in/khalo-monaheng-b6a821b0) | [Email](titus.khalomonaheng@gmail.com)

The Integration Pain Point: Older banks run on very old "legacy" computer systems. Your SaaS can act as a simple translator box. They send you their old data format, your software instantly cleans it and formats it into the complex ISO 20022 XML format, and sends it on. -->