# Corporate Policy Context Document
**Generated:** May 3, 2026  
**Source:** Consolidated from data folder markdown files

---

## Table of Contents
1. [IT Security & Data Privacy](#it-security--data-privacy)
2. [Learning & Development](#learning--development)
3. [Travel & Expense Policies](#travel--expense-policies)
4. [International Travel](#international-travel)
5. [HR Code of Conduct](#hr-code-of-conduct)
6. [Leave & Absences](#leave--absences)
7. [Performance & Compensation](#performance--compensation)

---

## IT Security & Data Privacy
**Document ID:** SEC-POL-8005-V7 | **Effective:** June 1, 2026

### Core Principles
- **Zero-Trust Architecture:** Access granted strictly on least privilege principle; continuous verification required
- **No Expectation of Privacy:** Organization monitors all network traffic and can inspect corporate hardware without notice

### Data Classification System (4 Tiers)
| Tier | Classification | Handling | Examples |
|------|---|---|---|
| 1 | Public | Unrestricted sharing | Marketing materials, press releases |
| 2 | Internal Use Only | Limited to approved cloud drives; NDA required for external sharing | Org charts, SOPs, meeting recordings |
| 3 | Confidential | Encrypted at rest/transit; strict need-to-know; emailing to personal accounts triggers DLP alert | Earnings reports, strategic roadmaps, source code, performance reviews |
| 4 | Restricted/Highly Sensitive | Secure database enclaves only; transferring via Slack/email is Level 3 violation | PII, credit card data, health records, unencrypted API keys |

### Key Policies
- **MFA Mandatory:** Hardware security keys (YubiKeys) preferred; SMS-based MFA prohibited
- **Password Requirements:** 14+ characters, cannot contain username or company name; rotated every 90 days
- **BYOD Protocol:** Personal phones require MDM software installation; organization can remotely wipe data
- **Shadow IT Prohibited:** No inputting Tier 2+ corporate data into public AI tools or unauthorized SaaS platforms
- **Incident Reporting SLAs:**
  - Lost/stolen hardware: 12 hours
  - Phishing click: 1 hour
  - Misdirected email with Tier 3/4 data: 4 hours
- **Amnesty Clause:** No disciplinary action for honest mistakes if reported immediately per SLAs
- **Access Revocation:** Immediate upon termination; hardware return required within 3 business days or cost deducted from final paycheck

---

## Learning & Development
**Document ID:** LND-POL-7010-V3 | **Effective:** May 1, 2026

### Mandatory Training
- All new hires must complete within 30 days: HR-101 (2 hrs), SEC-100 (1.5 hrs), FIN-201 (1 hr)
- Annual Security & Compliance Refresher: 60 minutes by October 31st
- Non-compliance results in immediate network access suspension and disciplinary action

### Professional Development Stipend (Annual, refreshes Jan 1)
| Job Level | Annual Limit | Approval |
|---|---|---|
| Individual Contributors (L1-L4) | $1,500 | Direct Manager |
| Management (M1-M2) | $3,000 | Department Director |
| Directors+ (D1+) | $5,000 | VP |

- Conference travel (flights, hotel, per diems) is separate from L&D stipend but subject to *Travel Policy*
- **Tech-Stack Exemption:** Engineers/Data Scientists/Product roles can request additional $2,000 for AI/ML topics (CTO approval required)

### Tuition Assistance Program (TAP)
**Eligibility:** 12+ months continuous service; Good Standing; degree related to current/future role

**Financial Limits:**
- Max $5,250 USD per calendar year (aligns with IRS Section 127)
- Non-reimbursable: Late fees, graduation fees, parking, optional materials
- Covers: Tuition, lab fees, required textbooks

**Academic Performance & Reimbursement:**
- **Undergrad:** A/B = 100%; C = 50%; D/F/Incomplete = 0%; Pass/Fail = Pass yields 100%
- **Graduate:** A/B = 100%; C and below = 0%

**Pre-Approval Required:** Submit Tuition Approval Form to manager/HR at least 15 days before course start

**Clawback Clause - Repayment Schedule (if terminated):**
- 0-12 months: Repay 100%
- 12-24 months: Repay 50%
- 24+ months: 0% repayment required
- Deducted from final paycheck if applicable

---

## Travel & Expense Policies

### Standard Domestic Travel
**Document ID:** TRV-POL-1001-V4 | **Effective:** January 1, 2026

#### Pre-Approval Matrix
| Trip Cost | Primary Approval | Secondary Approval | Lead Time |
|---|---|---|---|
| $0-$999 | Direct Manager | None | 7 days |
| $1,000-$2,999 | Director | None | 14 days |
| $3,000-$9,999 | VP | Finance Controller | 21 days |
| $10,000+ | C-Suite | CFO | 30 days |

**Must book via:** TripIt Corporate Navigator or Travel Management Company (TMC); never Expedia, Kayak, personal loyalty programs

#### Air Travel
- **Under 6 hours:** Economy Class only
- **6+ hours (domestic):** Premium Economy approved; Business Class for C-Suite with CFO exception letter
- **Baggage:** 1 checked bag reimbursed; 2 bags if 7+ consecutive days
- **In-Flight Wi-Fi:** Reimbursable for 2+ hour flights

#### Ground Transportation
- **Rental Cars:** Intermediate/Standard class via Enterprise or National; must decline CDW/LIS
- **Rideshare:** UberX/Lyft Standard; premium tiers only if client present
- **Personal Vehicle Mileage:** IRS standard rate ($0.67/mile for 2026); normal commute distance deducted

#### Lodging - City Tier Limits (excluding taxes/resort fees)
| Tier | Examples | Max Nightly Rate |
|---|---|---|
| Tier 1 (Premium) | NYC, SF, Boston, DC, LA | $375 |
| Tier 2 (Major) | Chicago, Seattle, Austin, Denver, Miami, Atlanta | $285 |
| Tier 3 (Standard) | All other locations | $195 |

- Alternative accommodations (Airbnb) permitted if total < threshold and stay 5+ consecutive nights (needs Director approval)

#### Meals & Per Diems
- **Employee Per Diem:** $85/day full day; $63.75 prorated first/last day (no receipts required)
- **Provided meals deduct:** Breakfast -$20, Lunch -$25, Dinner -$40
- **Alcohol:** Non-reimbursable for employee-only travel
- **Client Entertainment:** $150 USD/attendee max; receipts required; must include attendee names/titles/business purpose

#### Submission Timeline
- Within 30 days of trip end
- 30-60 days: Requires VP Finance written justification
- After 60 days: Permanently denied; employee personally liable

#### Non-Reimbursable Expenses
- Airline club memberships, childcare, traffic/parking fines, personal grooming, pay-per-view, clothing/luggage, gym fees, dependent travel costs

### Mileage & Fuel Reimbursement
**Document ID:** TRV-POL-3012-V2 | **Effective:** April 1, 2026

#### Standard Mileage Rate (SMR) Program
- **For:** Occasional business travel (<5,000 annual miles)
- **Current Rate:** $0.69/mile (effective Jan 1, 2026)
- **Covers:** Petrol, maintenance, insurance, depreciation
- **Prohibited:** Cannot claim fuel receipts if using mileage rate (fraud trigger)

#### Fixed and Variable Rate (FAVR) Allowance
- **For:** High-mileage drivers (5,000+ annual business miles)
- **Components:** Fixed monthly stipend ($450/month example) + Variable fuel rate ($0.18/mile example)
- **Adjusted by:** Employee's zip code (geographical equity)
- **Vehicle Compliance:** Max 7 years old; MSRP $25,000-$60,000; 100/300/50 insurance coverage minimum

#### Rental Vehicle Fuel
- Must refuel to full before return
- Corporate credit card required; no prepaid fuel option (premium markup)
- Refueling penalty difference deducted if under-refueled

#### Electric Vehicles
- **Personal EVs:** Still subject to SMR ($0.69/mile); cannot expense charging costs
- **Rental EVs:** Public charging (Tesla Supercharger, etc.) reimbursable; return with 70%+ charge

#### Normal Commute Deduction Rule
**Formula:** `(Total Miles) - (Normal Commute Miles) = Reimbursable Miles`

- Example: 40 miles to client site, 15-mile normal commute to office = (40 × 2) - 30 = 50 reimbursable miles
- Weekend/holiday travel: Entire mileage reimbursable (no commute deduction)

#### Tolls, Parking & Ancillary Costs
- Tolls reimbursable; no monthly transponder maintenance fees
- Valet parking reimbursable only if self-parking unavailable or safety risk
- Fines (parking tickets, speeding, toll evasion, towing) categorically non-reimbursable

#### Audit Triggers
- Round-number mileage claims
- Fuel receipts + mileage claims simultaneously
- Failure to deduct commute mileage
- Fuel gallons exceed vehicle tank capacity

---

## International Travel
**Document ID:** TRV-POL-2005-V3 | **Effective:** February 1, 2026

### Passport & Visa Requirements
- Passport valid 6+ months beyond return date
- Business visas required (not tourist visas); Level 1 violation to travel under false pretenses = immediate termination
- All costs fully reimbursable: consular fees, vendor processing, photos

### International Approval Matrix
| Category | Risk Level | Primary Approval | Secondary Approval | Lead Time |
|---|---|---|---|---|
| Standard | Low-Moderate | Director | VP | 30 days |
| High-Risk | High (Level 3/4) | VP | Chief Risk Officer | 45 days |
| Executive | Any | C-Suite Sponsor | General Counsel | 21 days |

### Air Travel - Class of Service by Flight Duration
- **Under 8 hours:** Economy Class
- **8-12 hours:** Premium Economy approved
- **Over 12 hours:** Business Class approved
- **Long layovers (14+ total hours):** Single airport lounge pass ($75 max) reimbursable

### Ground Transportation
- **Preferred:** High-speed rail (Europe, Japan) in developed regions
- **Prohibited regions for car rentals:** High road-risk countries (India, Brazil, Sub-Saharan Africa)
- **Approved regions:** Canada, UK, EU, Australia (with International Driving Permit)
- **Chauffeur services:** Mandatory in high-risk destinations via Global Security Dashboard

### Lodging
- Max rate: 120% of US State Department Foreign Per Diem Rate for specific city
- **Security requirements:** 24/7 front desk, internal deadbolts, peepholes, no ground-floor rooms (high-risk areas)
- Alternative accommodations (Airbnb, Vrbo) strictly prohibited

### Currency & Per Diems
- Convert using OANDA.com historical rates on transaction date
- Foreign transaction fees (3% max) reimbursable if using personal card
- International per diem based on WHO/State Department tables; no receipts required under threshold

### Health & Vaccinations
- 100% reimbursement for travel clinic and required/recommended immunizations (4+ weeks before departure)
- Medical evacuation covered via International SOS (ISOS) contract

### Data Security - High-Risk Destinations
- **Clean Device Program:** Prohibited from bringing corporate laptops/phones to High Cyber-Risk countries (China, Russia, Iran)
- Request "Burner" devices 14 days before travel; immediately returned/destroyed upon return
- Corporate VPN mandatory on public Wi-Fi; contact IT Security if VPN blocked by foreign firewall

### Critical Rules
- **90-Day Rule:** Cannot exceed 90 cumulative days in single foreign jurisdiction per 12-month period
- **Permanent Establishment (PE) Risk:** Signing contracts/generating revenue creates tax liability; must have contract authority limited to home country
- **Device Searches:** Comply with customs officials if demanded; report confiscation to CISO immediately

---

## HR Code of Conduct
**Document ID:** HR-POL-5050-V4 | **Effective:** March 1, 2026

### Reporting Mechanisms
- **Direct Manager:** Primary contact
- **HR Business Partner:** Interpersonal conflicts
- **Global Ethics Hotline:** 24/7, anonymous, 14 languages
- **Manager Obligation:** Managers must report Level 2/3 violations to HR within 24 hours (failure = Level 2 violation)

### Non-Retaliation Policy
- Absolute prohibition against termination, demotion, pay reduction, exclusion, hostile behavior for good-faith reporting
- Retaliation = immediate Level 3 action up to termination

### Investigation Protocols
- Confidential, need-to-know basis only
- Open investigation within 3 business days
- Conclusion within 30 days (barring legal complexity)
- Administrative leave may be imposed during investigation

### Policy Violation Categories

**Level 1: Minor Infractions** → Documented Verbal Warning
- Habitual tardiness, unexcused meeting absence, dress code violations, minor misuse of equipment

**Level 2: Moderate Misconduct** → Written Warning + PIP (Step 2)
- Insubordination, travel policy violations, aggressive communication, unauthorized internal document sharing, repeated Level 1s

**Level 3: Severe Misconduct** → Immediate Termination (bypasses progressive discipline)
- Expense fraud, physical violence, sexual harassment, corporate espionage, working under influence of illicit drugs, data sabotage

### Progressive Disciplinary Steps
1. **Documented Verbal Warning** → Note in file for 6 months
2. **Written Warning + Performance Improvement Plan (PIP)** → 30/60/90 days; ineligible for promo/transfer/bonus if failed
3. **Final Written Warning / Unpaid Suspension** → 1-3 days unpaid (jurisdiction-dependent); ineligible for benefits during 12-month period
4. **Termination for Cause** → Final escalation after progressive steps fail

### Zero-Tolerance Offenses (Immediate Termination)
- Expense fraud (fabricated receipts, personal expenses as corporate)
- Theft (physical, intellectual, digital property)
- Violence or weapons on premises
- Egregious harassment/discrimination

### Anti-Harassment & Non-Discrimination
- Protected classes: Race, color, religion, age, sex, national origin, disability, genetics, veteran status, sexual orientation, gender identity
- **Quid Pro Quo:** Promotion/hiring/raise contingent on sexual advances = strictly prohibited
- **Hostile Work Environment:** Severe/pervasive unwelcome conduct creating intimidating/abusive environment

### Conflicts of Interest
- **Outside Employment:** Prohibited if competes or interferes with job duties; requires HR written approval
- **Gifts from Vendors:** $50 USD/vendor/calendar year max; exceed = return or surrender to HR
- **Gifts to External Parties:** Follow Procurement Policy; government officials = immediate termination + legal prosecution (FCPA)

### Substance Abuse & Alcohol
- Illegal drugs on premises/during business = Level 3 violation
- Intoxication in office = Level 3 violation
- **Exceptions:** Approved corporate events (supplied by company) and client entertainment (30% of bill max)

### Appeals
- Submit written appeal to VP HR within 7 days of disciplinary action
- VP HR reviews files and renders final, binding decision within 14 days

---

## Leave & Absences
**Document ID:** HR-POL-4001-V6 | **Effective:** January 1, 2026

### Paid Time Off (PTO) - Accrual for Full-Time Employees

| Tenure | Annual Days | Bi-Weekly Accrual | Max Cap |
|---|---|---|---|
| 0-2 years | 15 days (120 hrs) | 4.61 hrs | 180 hrs |
| 3-5 years | 20 days (160 hrs) | 6.15 hrs | 240 hrs |
| 6-9 years | 25 days (200 hrs) | 7.69 hrs | 300 hrs |
| 10+ years | 30 days (240 hrs) | 9.23 hrs | 360 hrs |

**Part-Time:** Pro-rata basis (20-29 hrs/week); <20 hrs/week = no PTO

### PTO Carryover Rules
- **Standard:** Max 40 hours (5 days) rolls to next year; excess forfeited Dec 31
- **Exceptions (CA, CO, MT, NE):** No "use it or lose it"; subject to max accrual cap instead

### Global Holidays
- 10 designated holidays (US): New Year, MLK Jr. Day, Presidents' Day, Memorial Day, Juneteenth, Independence Day, Labor Day, Thanksgiving + 1 day after, Christmas
- Saturday holiday = observed Friday; Sunday holiday = observed Monday

### Floating Holidays
- 2 floating holidays (16 hrs) granted Jan 1 (lump sum, non-accruing)
- New hires after July 1: Only 1 floating holiday that year
- **Non-rollover; never paid out** upon termination

### Sick Leave
- **Front-loaded:** 80 hours (10 days) granted Jan 1
- **Non-rolling:** Unused does not carry to next year
- **Doctor's Note:** Required only if 3+ consecutive days used; failure to provide within 5 business days = unpaid leave

### Parental & Family Leave (6+ months service required)
- **Primary Caregiver:** 16 weeks at 100% pay
- **Secondary Caregiver:** 6 weeks at 100% pay
- **Intermittent:** Minimum 1-week blocks; must exhaust within 12 months of birth/placement

### Bereavement Leave
- **Tier 1 (Immediate Family - spouse, child, parent, sibling):** 5 paid days
- **Tier 2 (Extended Family - grandparent, grandchild, aunt/uncle, in-laws):** 3 paid days
- **Tier 3 (Miscarriage/Stillbirth):** 5 paid days

### Sabbatical Program
- **Eligibility:** 7 years continuous full-time service
- **Duration:** 4 weeks (20 business days), must be consecutive
- **Timing:** Must use within 24 months of 7-year anniversary or permanently forfeited
- **Benefits Continuation:** Salary, health/dental/retirement continue; no PTO accrual; equipment stipends suspended

### Civic Duty
- **Jury Duty:** Up to 10 business days at base salary; requires jury summons copy to HR within 48 hours; court stipends (excluding travel) must be remitted to company
- **Voting Leave:** 2 hours paid if insufficient time outside work hours

### Unpaid Leave of Absence (ULOA)
- Requires VP + Chief HR Officer approval
- Max 90 cumulative days per rolling 12-month period
- Employee pays 100% of healthcare premiums during ULOA

### Termination Payout
- **PTO:** Paid out at standard hourly rate in final paycheck
- **Negative balance:** Deducted from final paycheck (where legal)
- **Non-payable:** Sick Leave, Floating Holidays, Sabbatical, Bereavement never paid out

### Request Requirements
- **1-4 days PTO:** 7 days advance notice via Workday
- **5+ consecutive days:** 21 days advance notice + manager approval
- **Sick Leave:** 1 hour prior notice via phone/Slack

---

## Performance & Compensation
**Document ID:** HR-POL-6002-V5 | **Effective:** April 1, 2026

### Performance Review Cycle
- **H1 (Mid-Year):** June 1-July 15 → Development focus; no formal ratings or compensation adjustments
- **H2 (Year-End):** Nov 15-Jan 31 → Comprehensive evaluation; formal ratings assigned
- **Eligibility Cutoff:** Hired by Sept 30 to receive year-end rating; Oct 1+ = "Too New to Evaluate" (TN)

### 5-Point Rating Scale (Target Distribution)
- **Rating 5 (Exceptional):** Significantly exceeds all expectations (Top 10%)
- **Rating 4 (Exceeds Expectations):** Frequently exceeds goals and demonstrates high impact (25%)
- **Rating 3 (Successfully Meets Expectations):** Consistently delivers on all core goals (50%) *← Baseline*
- **Rating 2 (Inconsistent):** Meets some goals, falls short on others (10%)
- **Rating 1 (Unsatisfactory):** Fails to meet core role requirements (5%)

### Base Salary & Geographic Bands
- **Target:** 75th percentile of market rates (third-party benchmarking)
- **Geographic Tiers:** Tier A (Premium: SF, NYC, London, Zurich) = 100% | Tier B (Major: Chicago, Austin, Toronto, Sydney) = 85% | Tier C (Standard) = 75%
- **Relocation:** Salary adjusted downward if voluntarily relocating to lower-cost market (within 60 days)

### Merit Matrix
- Base increases determined by Performance Rating + Position in Range (PIR)
- Higher PIR employees receive smaller increases for same rating

### Annual Bonus Program
**Formula:** `(Base Salary) × (Target Bonus %) × (Company Multiplier) × (Individual Multiplier)`

**Target Bonus by Level:**
- Individual Contributors: 10%
- Managers: 15%
- Directors: 25%
- VPs: 40%

**Company Multiplier:** 0.0 to 1.5 based on corporate EBITDA achievement (Board-set)

**Individual Multiplier (by Rating):**
- Rating 5 = 1.3x
- Rating 4 = 1.1x
- Rating 3 = 1.0x
- Rating 2 = 0.5x
- Rating 1 = 0.0x (ineligible)

**Proration:** If hired Jan-Sept, bonus prorated based on days employed

**Eligibility for Payout:** Must be actively employed and in good standing on payout date (typically March); resignation Feb 28 = forfeited bonus

### Equity - Restricted Stock Units (RSUs)
- **New Hire Grants:** 4-year vesting with 1-year cliff (25% vests at 1-year anniversary; 75% in quarterly installments over next 36 months)
- **Annual Refresher Grants:** Eligible for Rating 3/4/5; quarterly vesting over 4 years (no cliff)
- **Executive Grants:** 3-year vesting with performance-based (PSU) milestones

### Promotion Criteria
- **Minimum Tenure:** 18 continuous months in current role (Engineering/Product: 12 months)
- **"Operating at Level" Requirement:** Must demonstrably perform higher-level duties for 3+ months before formal promotion request
- **Compensation on Promotion:** Minimum 25th percentile of new role band; if already exceeds, 8% promotional increase

### Off-Cycle Compensation Adjustments
- Heavily restricted; require VP + HR Business Partner approval
- Market adjustments if role falls below 50th percentile
- **No Counter-Offer Policy:** Managers prohibited from requesting off-cycle raises to retain departing employees

### Performance Improvement Plans (PIPs)
- Any employee on PIP or under Final Written Warning as of Nov 15 = ineligible for merit increase, annual bonus, or promotion

### Separation & Compensation Forfeiture
- **Bonus:** Forfeited if not actively employed/good standing on payout date
- **Unvested RSUs:** Immediately canceled and returned to equity pool at 5:00 PM on final employment date

---

## Key Cross-References & Relationships

### Policy Interdependencies
- **Travel Violations:** Can trigger Level 2 disciplinary action (Code of Conduct)
- **Security Violations:** Can trigger Level 3 immediate termination (Zero-Trust breaches, data loss)
- **Learning Benefits:** Subject to repayment if employee leaves within 24 months (TAP Clawback)
- **Performance Impact:** PIP placement blocks compensation increases, bonuses, and promotions
- **Bonus Eligibility:** Must be employed in good standing on payout date

### Common Audit Triggers
- Travel: Round-number mileage, dual fuel/mileage claims, commute deduction failures
- Expense: Vendor category misclassification, late submissions (60+ days), itemization missing
- Policy: Unauthorized software use, shadow IT, Tier 3+ data mishandling

### Mandatory Compliance Timeline
- **New Hires:** HR-101, SEC-100, FIN-201 within 30 days
- **Annual:** Security & Compliance Refresher by Oct 31
- **Travel Pre-Approval:** 7-30 days depending on cost
- **Expense Submission:** Within 30 days of trip end
- **Performance Review:** Mid-year June-July, Year-end Nov-Jan

---

**Document Last Updated:** May 3, 2026  
**For Official Policy Details:** Refer to full policy documents in project-aegis/data/ folder
