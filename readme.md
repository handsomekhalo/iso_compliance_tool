# RandRail - ISO 20022 Compliance Platform

A production-grade fintech platform for ISO 20022 payment reconciliation, 
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

The Integration Pain Point: Older banks run on very old "legacy" computer systems. Your SaaS can act as a simple translator box. They send you their old data format, your software instantly cleans it and formats it into the complex ISO 20022 XML format, and sends it on.