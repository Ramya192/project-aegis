# eval/golden_qa.py
"""
Golden QA dataset for Project Aegis — Enterprise RAG Evaluation.

15 question-answer pairs drawn directly from the 9 policy documents.
Covers all 5 policy categories: Travel, HR, IT, Finance (L&D), Compliance.

Each entry contains:
  - question       : realistic user query (as someone would type it)
  - expected_answer: key facts that MUST appear in a correct answer
  - source_doc     : document_id the answer comes from
  - category       : policy category (used to verify detect_category)
  - keywords       : minimum terms a correct answer must contain
"""

GOLDEN_QA = [
    # ── TRAVEL ──────────────────────────────────────────────────────────────
    {
        "id": "T001",
        "question": "What is the daily meal per diem for employees on domestic travel?",
        "expected_answer": "$85 per day for a full day, $63.75 for the first and last day (prorated). No receipts required.",
        "source_doc": "TRV-POL-1001-V4",
        "category": "Travel",
        "keywords": ["85", "63.75", "per diem", "prorated"],
    },
    {
        "id": "T002",
        "question": "What is the hotel limit per night for a trip to New York City?",
        "expected_answer": "$375 per night (Tier 1 Premium city). Taxes and resort fees are excluded from this cap.",
        "source_doc": "TRV-POL-1001-V4",
        "category": "Travel",
        "keywords": ["375", "Tier 1", "NYC"],
    },
    {
        "id": "T003",
        "question": "Can I book flights on Expedia for a business trip?",
        "expected_answer": "No. All bookings must be made via TripIt Corporate Navigator or an approved Travel Management Company (TMC). Personal booking platforms like Expedia or Kayak are not permitted.",
        "source_doc": "TRV-POL-1001-V4",
        "category": "Travel",
        "keywords": ["TripIt", "TMC", "Expedia", "not permitted"],
    },
    {
        "id": "T004",
        "question": "What is the mileage reimbursement rate if I use my personal car for a business trip?",
        "expected_answer": "The Standard Mileage Rate (SMR) is $0.69 per mile (effective Jan 1, 2026) for occasional business travel under 5,000 annual miles. Normal commute distance must be deducted from the total.",
        "source_doc": "TRV-POL-3012-V2",
        "category": "Travel",
        "keywords": ["0.69", "mileage", "commute", "deducted"],
    },
    {
        "id": "T005",
        "question": "How many days do I have to submit an expense report after a trip?",
        "expected_answer": "Within 30 days of the trip end. Submissions between 30-60 days require VP Finance written justification. After 60 days, the claim is permanently denied and the employee is personally liable.",
        "source_doc": "TRV-POL-1001-V4",
        "category": "Travel",
        "keywords": ["30 days", "60 days", "denied", "VP Finance"],
    },
    # ── HR / LEAVE ───────────────────────────────────────────────────────────
    {
        "id": "H001",
        "question": "How much parental leave does a primary caregiver get?",
        "expected_answer": "16 weeks at 100% pay for the primary caregiver. Requires 6+ months of service. Leave must be used in minimum 1-week blocks and exhausted within 12 months of birth or placement.",
        "source_doc": "HR-POL-4001-V6",
        "category": "HR",
        "keywords": ["16 weeks", "100%", "primary caregiver"],
    },
    {
        "id": "H002",
        "question": "How many PTO days do I get after 5 years of service?",
        "expected_answer": "Employees with 3-5 years of tenure receive 20 days (160 hours) annually, accruing at 6.15 hours per bi-weekly pay period, with a maximum cap of 240 hours.",
        "source_doc": "HR-POL-4001-V6",
        "category": "HR",
        "keywords": ["20 days", "160 hours", "6.15"],
    },
    {
        "id": "H003",
        "question": "What happens to unused sick leave at the end of the year?",
        "expected_answer": "Unused sick leave does not carry over to the next year. It is front-loaded at 80 hours on January 1 each year and is non-rolling. It is also never paid out upon termination.",
        "source_doc": "HR-POL-4001-V6",
        "category": "HR",
        "keywords": ["front-loaded", "80 hours", "not carry", "non-payable"],
    },
    {
        "id": "H004",
        "question": "How long is bereavement leave for the death of a grandparent?",
        "expected_answer": "3 paid days. Grandparents fall under Tier 2 (Extended Family), which covers grandparent, grandchild, aunt/uncle, and in-laws.",
        "source_doc": "HR-POL-4001-V6",
        "category": "HR",
        "keywords": ["3 paid days", "Tier 2", "grandparent"],
    },
    # ── IT SECURITY ──────────────────────────────────────────────────────────
    {
        "id": "S001",
        "question": "What are the password requirements under the IT security policy?",
        "expected_answer": "Passwords must be at least 14 characters, cannot contain the username or company name, and must be rotated every 90 days.",
        "source_doc": "SEC-POL-8005-V7",
        "category": "IT",
        "keywords": ["14 characters", "90 days", "username"],
    },
    {
        "id": "S002",
        "question": "How soon must I report a phishing click to the security team?",
        "expected_answer": "Within 1 hour of the phishing click. The Amnesty Clause applies — no disciplinary action if reported honestly and within the required SLA.",
        "source_doc": "SEC-POL-8005-V7",
        "category": "IT",
        "keywords": ["1 hour", "phishing", "Amnesty"],
    },
    {
        "id": "S003",
        "question": "Can I use ChatGPT or other public AI tools for work tasks?",
        "expected_answer": "No. Inputting Tier 2 or higher corporate data into public AI tools is prohibited under the Shadow IT policy. This includes unauthorized SaaS platforms.",
        "source_doc": "SEC-POL-8005-V7",
        "category": "IT",
        "keywords": ["Shadow IT", "prohibited", "Tier 2", "AI tools"],
    },
    # ── LEARNING & DEVELOPMENT ───────────────────────────────────────────────
    {
        "id": "L001",
        "question": "What is the annual professional development budget for an individual contributor?",
        "expected_answer": "$1,500 per year for Individual Contributors (L1-L4), approved by their Direct Manager. The budget refreshes on January 1 each year. Engineers and Data Scientists can request an additional $2,000 for AI/ML topics with CTO approval.",
        "source_doc": "LND-POL-7010-V3",
        "category": "HR",
        "keywords": ["1,500", "L1-L4", "Direct Manager", "2,000"],
    },
    {
        "id": "L002",
        "question": "If I leave the company 8 months after receiving tuition assistance, how much do I repay?",
        "expected_answer": "100% repayment is required if terminated within 0-12 months of receiving tuition assistance. The amount will be deducted from the final paycheck if applicable.",
        "source_doc": "LND-POL-7010-V3",
        "category": "HR",
        "keywords": ["100%", "12 months", "final paycheck"],
    },
    # ── PERFORMANCE & COMPENSATION ───────────────────────────────────────────
    {
        "id": "P001",
        "question": "What is the annual bonus for a manager with a Rating 4 if the company multiplier is 1.2?",
        "expected_answer": "Formula: Base Salary × 15% (Manager target) × 1.2 (Company) × 1.1 (Rating 4 individual multiplier). For example, on a $100,000 base: $100,000 × 0.15 × 1.2 × 1.1 = $19,800.",
        "source_doc": "HR-POL-6002-V5",
        "category": "HR",
        "keywords": ["15%", "1.1", "1.2", "formula", "multiplier"],
    },
]
