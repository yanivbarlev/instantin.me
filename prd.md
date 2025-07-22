\# Product Requirements Document: Link‑in‑Bio Commerce Platform



\## 1. Introduction / Overview



Late‑comer creators need a friction‑free way to monetize their social traffic without rebuilding from scratch. This platform gives them a link‑in‑bio page that sells digital products, physical goods, services and memberships. Key differentiators:



\* \*\*One‑click migration wizard\*\* imports an existing Linktree, Stan.store or similar page and produces an equivalent store in under 30 seconds.

\* \*\*Instant AI page builder\*\* converts a short text list of offers (or a single social‑media URL) into a fully designed, branded storefront.

\* \*\*Collaborative drops\*\* let multiple creators bundle offers into a shared flash‑sale page with automatic revenue splits.

\* \*\*Monthly raffle programme\*\* rewards creators with cash prizes proportional to the traffic they drive.



\## 2. Goals



1\. Achieve \*\*1 000 monthly active creators (MAC)\*\* within 6 months of launch.

2\. Import‐success rate ≥ 90 % for pages migrated via the wizard.

3\. Time from sign‑up to published storefront ≤ 5 minutes for 80 % of new users.

4\. Process ≥ US \\$50 k GMV in the first 3 months.



\## 3. User Stories



| ID    | Story                                                                                                                                                   |

| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |

| US‑01 | As a \*non‑technical solo creator\*, I want to paste my existing Linktree URL so that my new page is ready instantly.                                     |

| US‑02 | As a \*coach with multiple offers\*, I want to type my service list and have the system produce a polished storefront so that I avoid manual design work. |

| US‑03 | As a \*pair of influencers\*, we want to launch a joint bundle with automatic profit split so that collaboration is hassle‑free.                          |

| US‑04 | As a \*creator\*, I want earnings to settle the same day via Stripe or PayPal so that I keep healthy cash flow.                                           |

| US‑05 | As a \*creator\*, I want to see my raffle tickets count rise with traffic so that I feel motivated to promote my store.                                   |



\## 4. Functional Requirements



1\. \*\*Account \& Auth\*\*

&nbsp;  1.1 The system shall support email + social log‑in (Google, Apple).

&nbsp;  1.2 The system shall enforce 2‑factor authentication via email code.

2\. \*\*Storefront Creation Modes\*\*

&nbsp;  2.1 \*\*Manual Builder\*\*: drag‑and‑drop blocks (header, product, link, contact, scheduler).

&nbsp;  2.2 \*\*Instant AI Builder\*\*: user provides (a) free‑form offer list OR (b) social post URL. The system must:

&nbsp;  \\\* parse offers, price suggestions, images.

&nbsp;  \\\* generate a preview within 10 seconds.

&nbsp;  2.3 \*\*One‑click Migration\*\*: The user needs to answer what his main goal is (Maximize revenues, enhanced style, maximize traffic,other ) user inputs competitor page URL; system fetches public data, maps to internal blocks, and enhances the current page based on the prefrences + showing by how much the main goal will improve as well as editable preview. 

3\. \*\*Product Types\*\*

&nbsp;  3.1 Digital downloads (files up to 5 GB).

&nbsp;  3.2 Physical goods (shipping rules, inventory tracking).

&nbsp;  3.3 Services (calendar booking + payment).

&nbsp;  3.4 Memberships/subscriptions (recurring billing).

&nbsp;  3.5 Tips/donations.

4\. \*\*Payments\*\*

&nbsp;  4.1 The system shall integrate Stripe and PayPal for checkout and payouts.

&nbsp;  4.2 Payouts shall be triggered daily; creators choose Stripe Connect Express or PayPal Payouts.

&nbsp;  4.3 Transaction fees are displayed prior to confirmation.

5\. \*\*Collaborative Drops\*\*

&nbsp;  5.1 Creators can invite others via email to a drop.

&nbsp;  5.2 Revenue split percentages must total 100 % and are stored on the drop record.

&nbsp;  5.3 On purchase, the system shall route payouts to each participant according to the split.

6\. \*\*Monthly Raffle\*\*

&nbsp;  6.1 Each unique visitor = 1 raffle ticket for that creator.

&nbsp;  6.2 On the first day of each month, pick 10 winners weighted by ticket count.

&nbsp;  6.3 Prize pool is 5 % of prior month platform fees but no less than $500; distributed equally among winners.

&nbsp;  6.4 Winners are notified by email and dashboard banner.

7\. \*\*Analytics\*\*

&nbsp;  7.1 Dashboard shows page views, product views, sales, conversion rate.

&nbsp;  7.2 Data refresh latency ≤ 5 minutes.

8\. \*\*Fraud Prevention \& Refunds\*\*

&nbsp;  8.1 Stripe Radar and PayPal fraud scores must be logged.

&nbsp;  8.2 Orders flagged by provider are held for manual review.

&nbsp;  8.3 Creator‑initiated refunds are supported from the dashboard.

9\. \*\*Scalability \& Performance\*\*

&nbsp;  9.1 Storefront render time ≤ 1 second median.

&nbsp;  9.2 System must handle 10 k concurrent visitors without degraded performance.

10\. \*\*Compliance \& Security\*\*

&nbsp;   10.1 GDPR data export/delete features.

&nbsp;   10.2 PCI‑DSS handled by Stripe/PayPal; no raw card data stored.



\## 5. Non‑Goals (Out of Scope for v1)



\* Advanced traffic‑source attribution beyond basic UTM capture.

\* In‑depth funnel analytics or A/B testing tools.

\* Multi‑language UI (English only in v1).



\## 6. Design Considerations



\* Mobile‑first responsive layout (≥ 70 % traffic expected from mobile).

\* Theme presets: Light, Dark, Creator‑brand colour picker.

\* Components follow Tailwind utility classes for rapid theming.

* SEO optimized



\## 7. Technical Considerations



\* \*\*Stack\*\*: Python 3.12, FastAPI, Jinja templates, PostgreSQL on PythonAnywhere.

\* \*\*AI services\*\*: Kimi k2 using groq api; Unsplash API for placeholder images.

\* \*\*Background tasks\*\*: Celery + Redis (running on AWS Elasticache) for raffle selection and payouts.

\* \*\*File storage\*\*: AWS S3 via boto3 for digital downloads and media.



\## 8. Success Metrics



\* KPI‑1: Monthly active creators (MAC). Target 1 000 by month 6.

\* KPI‑2: Average time to live storefront ≤ 5 minutes.

\* KPI‑3: Import wizard success ≥ 90 %.



\## 9. Open Questions



1\. What legal terms and conditions will govern the raffle to meet regional regulations?

2\. Do we need custom domain support in v1 or defer to v1.1?

3\. Should collaborative drops support more than two creators initially?

4\. Maximum file size and storage tier pricing for digital products?

5\. Will mobile apps be required, or is PWA sufficient?



