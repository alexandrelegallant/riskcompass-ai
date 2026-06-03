## Live Demo

[Open RiskCompass AI](https://riskcompass-ai-dfy54feghdkphcsg9ov9fv.streamlit.app/)

# 🧭 RiskCompass AI
### WA Government Cyber Threat Prioritisation Tool
> Bloom × CyberWest Hub × WA Office of Digital Government Hackathon

---

## The Problem
WA Government agencies receive a constant stream of vulnerability reports, threat intel, and security alerts. With limited resources, **prioritising the right work is harder than finding the risks themselves.**

## The Solution
RiskCompass AI is a human-in-the-loop decision-support tool that:
1. **Ingests** alerts via CSV upload or paste
2. **Scores** each alert (0–100) using a transparent rule-based engine (CVSS + exploitability + exposure + asset criticality + policy impact)
3. **Ranks** alerts into CRITICAL / HIGH / MEDIUM / LOW with WA-policy-mapped timeframes
4. **Enriches** with Claude AI explanations, recommended actions, and an executive summary
5. **Flags** which alerts require DGov escalation
6. **Visualises** the threat landscape across an interactive dashboard
7. **Answers** analyst questions in natural language

---

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...

# Run
streamlit run app.py
```
Opens at **http://localhost:8501**

> **No API key?** The app still works — rule-based scoring runs entirely offline.

---

## Architecture

```
CSV / paste input
      ↓
Rule-based scoring engine  (scoring.py)
  · CVSS weight (40 pts max)
  · Active exploitation (+20 pts)
  · Internet-facing (+15 pts)
  · Sensitive data (+10 pts)
  · Business criticality (+10 pts)
  · No patch available (+5 pts)
      ↓
WA Policy mapping
  · Timeframe obligation (48hrs, 24hrs, Immediate)
  · Policy section reference
  · DGov escalation flag
      ↓
Claude AI enrichment (optional)
  · Per-alert recommended actions
  · Business impact statements
  · Executive summary
  · Action plan with owners
      ↓
Streamlit UI
  · Prioritised alert list
  · Interactive dashboard (Plotly)
  · AI chat interface
  · CSV export
```

---

## Scoring Formula

```
Priority Score =
  (CVSS / 10) × 40           # base severity
  + 20 if actively exploited  # highest urgency
  + 12 if exploit available   # known weaponised
  + 15 if internet-facing     # exposure
  + 10 if sensitive data       # impact
  + 0–10 for asset criticality
  + 5 if no patch available

Score ≥ 80 → CRITICAL → Immediate
Score ≥ 60 → HIGH     → Within 24 hours
Score ≥ 40 → MEDIUM   → Within 48 hours
Score  < 40 → LOW     → Within 2 weeks
```

---

## WA Cyber Security Policy Alignment

| Policy Section | How RiskCompass Helps |
|---|---|
| 1.7 Vulnerability Management | Enforces 48hr SLA for critical CVEs |
| 3.1.1 Essential Eight | Maps every alert to E8 control gaps |
| 3.6 Identity & Access Management | Flags MFA/access control gaps |
| 4.1 Adverse Event Analysis | Structured triage output for all events |
| 5.1 Incident Management | Flags DGov escalation obligations |
| 5.3 Ransomware Position | Immediate escalation logic |

---

## Pitch Framing

> *"Agencies don't lack alerts — they lack a prioritised signal. RiskCompass AI turns a wall of noise into a ranked, policy-mapped, human-in-the-loop action list that any analyst can act on immediately — even without an AI connection."*

Key differentiators for judges:
- **Transparent scoring** — not a black box; every score is explainable
- **Demo-resilient** — works fully offline via rule-based engine
- **Policy-native** — built around WA Cyber Security Policy 2024 obligations
- **Human-in-the-loop** — AI assists, humans decide (government-safe framing)
- **DGov-centric** — designed to help ODG improve visibility across all agencies
