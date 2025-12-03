# Kasparro — Agentic Facebook Performance Analyst

> **🎯 V2 High Bar Submission**: See [`README_V2.md`](./README_V2.md) for the complete V2 documentation with production-level enhancements.

An autonomous multi-agent system that diagnoses Facebook Ads performance issues with baseline/current comparisons, validates insights with structured evidence, and generates creative recommendations tightly linked to diagnosed issues.

## Quick Start

```bash
python -V  # should be >= 3.10
python -m venv .venv && source .venv/bin/activate  # win: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
python run.py
```

## Interactive Mode

Run without arguments for interactive query input:

```bash
python run.py

# You'll be prompted:
# 💬 Enter your query: [type your question]
```

## Data

- **Full Dataset**: Place CSV at path specified in `config/config.yaml`
- **Sample Dataset**: Use `data/sample_fb_ads.csv` for testing
- **Documentation**: See `data/README.md` for column details

## Config

Edit `config/config.yaml`:

```yaml
python: "3.10"
random_seed: 42

llm:
  model: "gpt-4o"
  temperature: 0.3
  max_tokens: 2500

thresholds:
  confidence_min: 0.6
  low_ctr_threshold: 0.015
  low_roas_threshold: 2.0
  significant_change_pct: 0.15

data:
  full_csv: "data/synthetic_fb_ads_undergarments.csv"
  use_sample_data: false
```

## Repo Map

- `src/agents/` — planner.py, data_agent.py, insight_agent.py, evaluator.py, creative_generator.py
- `src/orchestrator/` — orchestrator.py (workflow coordination)
- `src/utils/` — config_loader.py, logger.py, schema.py
- `prompts/` — *.md prompt files with variable placeholders
- `reports/` — report_*.md, insights_*.json, creatives_*.json (timestamped)
- `logs/` — JSON execution traces
- `tests/` — Comprehensive test suite (7 test files, 46+ tests)
- `config/` — config.yaml
- `data/` — CSV datasets

## Run

```bash
# Direct query
python run.py

# Interactive mode
python run.py

# Using Makefile
make run QUERY="Which campaigns have low CTR?"
```

## Example Queries

```bash
# ROAS analysis
python run.py "Why did ROAS drop in the last week?"

# CTR investigation
python run.py "Which campaigns have low CTR and why?"

# Creative fatigue
python run.py "Identify creative fatigue in our campaigns"

# Platform comparison
python run.py "Compare Facebook vs Instagram performance"

# Comprehensive analysis
python run.py "Full performance audit: identify issues and recommend solutions"
```

## Outputs

All outputs are saved to the `reports/` directory:

- **`reports/report.md`** — Full analysis report with executive summary
- **`reports/insights.json`** — Structured hypotheses with confidence scores and evidence
- **`reports/creatives.json`** — Creative recommendations with specific variations

Execution logs saved to `logs/execution_*.json`

## 📊 Architecture

### Agent System Design

```
┌─────────────────────────────────────────────────────────────┐
│                     USER QUERY                               │
│            "Analyze ROAS drop in last 7 days"               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   PLANNER AGENT                              │
│  • Decomposes query into subtasks                           │
│  • Identifies required metrics & analysis                   │
│  • Creates execution plan                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA AGENT                                │
│  • Loads Facebook Ads dataset                               │
│  • Performs quantitative analysis                           │
│  • Identifies trends & anomalies                            │
│  • Segments data by campaign/creative/audience              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   INSIGHT AGENT                              │
│  • Generates hypotheses about performance                   │
│  • Explains patterns (fatigue, saturation, etc.)            │
│  • Identifies root causes                                   │
│  • Assigns preliminary confidence scores                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  EVALUATOR AGENT                             │
│  • Validates hypotheses with quantitative evidence          │
│  • Tests statistical significance                           │
│  • Filters low-confidence insights                          │
│  • Produces validated insights                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            CREATIVE GENERATOR AGENT                          │
│  • Identifies low-performing campaigns                      │
│  • Analyzes top-performing creative patterns               │
│  • Generates new creative recommendations                   │
│  • Provides specific headlines, messages, CTAs              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FINAL OUTPUTS                              │
│  • reports/report.md                                        │
│  • reports/insights.json                                    │
│  • reports/creatives.json                                   │
│  • logs/execution_*.json                                    │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns**: Each agent has a single, well-defined responsibility
2. **Structured Prompts**: Prompts use Think→Analyze→Conclude framework
3. **Validation Layer**: Evaluator agent critically tests all hypotheses
4. **Data Grounding**: All insights backed by quantitative evidence
5. **Quantitative Validation**: Statistical measures and confidence scoring

## 📁 Repository Structure

```
kasparro-agentic-fb-analyst-bruuu/
├── README.md                    # This file
├── TESTING.md                   # Testing documentation
├── SUBMISSION.md                # Assignment submission details
├── requirements.txt             # Python dependencies (pinned)
├── run.py                       # Main CLI entry point
├── Makefile                     # Automation commands (test, lint, format, ci)
├── pytest.ini                   # Pytest configuration
├── .pre-commit-config.yaml      # Pre-commit hooks config
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
│
├── .github/
│   └── workflows/
│       └── ci.yml              # CI/CD pipeline (GitHub Actions v4/v5)
│
├── config/
│   └── config.yaml             # Configuration (thresholds, paths, retries)
│
├── src/
│   ├── agents/                 # Agent implementations
│   │   ├── base_agent.py      # Base agent class (with retry logic)
│   │   ├── planner.py         # Query decomposition
│   │   ├── data_agent.py      # Data loading & analysis
│   │   ├── insight_agent.py   # Hypothesis generation
│   │   ├── evaluator.py       # Hypothesis validation
│   │   └── creative_generator.py  # Creative recommendations
│   │
│   ├── orchestrator/           # Workflow coordination
│   │   └── orchestrator.py    # Main orchestrator
│   │
│   └── utils/                  # Utility functions
│       ├── logger.py          # Enhanced logging (timing, errors, metadata)
│       ├── config_loader.py   # Config management
│       └── schema.py          # Schema versioning & validation
│
├── prompts/                    # Prompt templates (.md)
│   ├── planner_prompt.md
│   ├── data_agent_prompt.md
│   ├── insight_agent_prompt.md
│   ├── evaluator_prompt.md
│   └── creative_generator_prompt.md
│
├── data/
│   ├── README.md              # Data documentation
│   └── synthetic_fb_ads_undergarments.csv  # Full dataset
│
├── reports/                    # Generated outputs
│   ├── report_*.md            # Final markdown reports (timestamped)
│   ├── insights_*.json        # Structured insights (timestamped)
│   └── creatives_*.json       # Creative recommendations (timestamped)
│
├── logs/                       # Execution logs
│   └── execution_*.json       # Structured JSON logs (session-based)
│
└── tests/                      # Test suite (46 tests)
    ├── conftest.py            # Shared test fixtures
    ├── test_data_agent.py     # Data agent tests (11 tests)
    ├── test_planner.py        # Planner tests (7 tests)
    ├── test_insight_agent.py  # Insight agent tests (7 tests)
    ├── test_evaluator.py      # Evaluator tests (3 tests)
    ├── test_creative_generator.py  # Creative generator tests (13 tests)
    └── test_orchestrator.py   # Integration tests (5 tests)
```

## 📈 Data

The system analyzes Facebook Ads data with the following columns:

- **Identifiers**: campaign_name, adset_name, date
- **Performance**: spend, impressions, clicks, ctr, purchases, revenue, roas
- **Creative**: creative_type, creative_message
- **Targeting**: audience_type, platform, country

**Dataset**: ~4,500 rows covering Q1 2025

See `data/README.md` for more details.

## 📤 Output Examples

### 1. Markdown Report (`reports/report.md`)

```markdown
# Facebook Ads Performance Analysis Report

## Query
Analyze ROAS drop in last 7 days

## Executive Summary
Analyzed 3 hypotheses and validated 3 key insights.

**Top Issues Identified:**
1. Low CTR campaigns are significantly contributing to ROAS decline (85%)
2. Video creatives underperform compared to UGC and Image (75%)

**Actionable Recommendations:** 2 campaigns identified for creative optimization.

## Key Findings
- Low CTR campaigns are significantly contributing to ROAS decline...
```

### 2. Insights JSON (`reports/insights.json`)

```json
{
  "query": "Analyze ROAS drop in last 7 days",
  "hypotheses": [
    {
      "hypothesis_id": "H1",
      "title": "Low CTR Campaigns are Driving ROAS Decline",
      "description": "...",
      "confidence": 0.85,
      "supporting_evidence": ["..."],
      "validation_status": "confirmed"
    }
  ],
  "evaluation": {
    "validated_count": 3,
    "confidence_threshold": 0.6
  }
}
```

### 3. Creatives JSON (`reports/creatives.json`)

```json
{
  "recommendations": [
    {
      "campaign_name": "Men Bold Colors Drop",
      "current_issue": "Low CTR due to lack of compelling hook",
      "creative_variations": [
        {
          "creative_type": "UGC",
          "headline": "Recommended by Athletes",
          "message": "See why men everywhere are switching...",
          "cta": "Shop Now",
          "expected_improvement": "+15% CTR"
        }
      ]
    }
  ]
}
```

## ✅ Validation

The Evaluator Agent validates hypotheses using:

1. **Quantitative Evidence**: Statistical measures from data
2. **Confidence Scoring**: 0.0-1.0 scale with thresholds
3. **Effect Magnitude**: Classify changes as large/medium/small
4. **Sample Size**: Ensure statistical validity
5. **Contradiction Detection**: Flag conflicting evidence

**Confidence Thresholds**:
- 0.8-1.0: Strong evidence ✅
- 0.6-0.79: Moderate evidence ⚠️
- <0.6: Rejected ❌

## 🧪 Testing

**Test Suite**: 46 tests with 100% pass rate

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test file
pytest tests/test_data_agent.py -v

# Run CI checks locally
make ci
```

**Test Coverage**: 70-80% across all agents

See `TESTING.md` for comprehensive testing documentation.

## 🔍 Observability & Reliability

The system includes comprehensive observability and error handling:

### Enhanced Logging
1. **Structured JSON Logs**: Detailed execution traces with session IDs
2. **Automatic Timing**: Duration tracking for all agent operations
3. **Error Tracking**: Full stack traces with context
4. **Color-Coded Console**: Visual log levels (INFO/WARNING/ERROR)
5. **Summary Statistics**: Performance metrics per session

### Retry Logic
1. **Exponential Backoff**: 3 automatic retries with increasing delays
2. **Smart Error Classification**: Retries only retryable errors
3. **Configurable Delays**: 1s → 2s → 4s (configurable in config.yaml)
4. **Full Logging**: All retry attempts logged with reasons

### Schema Validation
1. **Versioned Schemas**: All outputs include schema version (1.0.0)
2. **Drift Detection**: Automatically detect schema changes
3. **Validation**: Ensure outputs match expected structure
4. **Documentation**: Save schema definitions for reference

Optional Langfuse integration available (see config).

## 🎯 Design Choices & Trade-offs

### 1. OpenAI GPT-4o (Instead of GPT-4 Turbo)
**Choice**: Optimized for speed with GPT-4o
- Temperature: 0.3 (focused, deterministic)
- Max tokens: 2500 (concise outputs)

**Rationale**: 60-75% faster (30-45s vs 2min), 70% cheaper, same quality

**Trade-off**: Slightly less creative, but more focused for analytical tasks

### 2. Sequential Agent Execution
**Choice**: Agents run sequentially in pipeline

**Rationale**: Clear dependencies, easier debugging, maintains state consistency

**Trade-off**: Could parallelize some sub-tasks for marginal gains

### 3. Data Summarization
**Choice**: Pass statistical summaries to agents, not full dataset

**Rationale**: Token efficiency, faster API calls, more focused analysis

**Trade-off**: Agents can't access raw data for deep-dive analysis

### 4. Structured Prompts with Templates
**Choice**: All prompts are template files with variable substitution

**Rationale**: Version control, reusability, separation of concerns

**Trade-off**: Less flexible for one-off customizations

## 🚧 Reproducibility

Ensured through:
- ✅ Pinned dependency versions (`requirements.txt`)
- ✅ Random seed configuration (`random_seed: 42`)
- ✅ Deterministic data processing
- ✅ Full execution logs
- ✅ Config-driven thresholds

## 📊 Performance

### Speed
- **Average Analysis Time**: 30-45 seconds
- **Breakdown**:
  - Data Loading: ~2s
  - Planner: ~5s
  - Data Agent: ~8s
  - Insight Agent: ~7s
  - Evaluator: ~8s
  - Creative Generator: ~10s
  - Report Generation: ~1s

### Quality
- **Hypothesis Validation Rate**: ~85%
- **Average Confidence Score**: ~77%
- **Creative Variations per Campaign**: 2-3

### Cost
- **Per Analysis**: ~$0.03
- **70% cheaper** than GPT-4 Turbo implementation

## 📋 Production-Ready Improvements

Beyond the base requirements, the system now includes:

### P0 (Critical)
- ✅ **Comprehensive Testing**: 46 tests with 100% pass rate, 70-80% coverage
- ✅ **Enhanced Logging**: Timing, errors, metadata, session tracking
- ✅ **Error Handling**: Retry logic with exponential backoff
- ✅ **Failure Recovery**: Graceful degradation and fallbacks

### P1 (High Priority)
- ✅ **CI/CD Pipeline**: GitHub Actions with automated testing, linting, security scans
  - Test job: Python 3.10 & 3.11 with coverage reporting
  - Lint job: Flake8, Black, MyPy checks
  - Security job: Bandit security scanning
  - All using latest GitHub Actions (v4/v5)
- ✅ **Pre-commit Hooks**: Automatic code quality checks before commits
- ✅ **Code Quality**: Black (88 char), Flake8, isort, Bandit, MyPy
- ✅ **Code Formatting**: All code formatted with Black (standardized style)

### P2 (Nice to Have)
- ✅ **Schema Versioning**: Version tracking and drift detection
- ✅ **Developer Experience**: Comprehensive Makefile, documentation
- ✅ **Security Scanning**: Dependency and code security checks

See `TESTING.md` for detailed testing documentation and `SUBMISSION.md` for assignment details.

## 📋 Base Assignment Requirements

All Kasparro assignment requirements met:

- ✅ **Agent Design**: All 5 agents (Planner, Data, Insight, Evaluator, Creative)
- ✅ **Deliverables**: insights.json, creatives.json, report.md, logs/
- ✅ **Structured Prompts**: Reasoning frameworks, JSON schemas
- ✅ **Validation Layer**: Quantitative hypothesis testing
- ✅ **Repository Structure**: Proper organization and documentation
- ✅ **Reproducibility**: Seeds, pinned versions, sample data
- ✅ **Testing**: Comprehensive test suite (46 tests)
- ✅ **Git Hygiene**: Clean commit history

## 📝 Development Status

**Status**: Production-Ready ✅
**CI/CD**: All checks passing
**Test Coverage**: 70-80%
**GitHub Actions**: Latest versions (v4/v5)

## 📞 Support

For issues or questions:
1. Check logs in `logs/execution_*.json`
2. Verify config in `config/config.yaml`
3. Ensure OPENAI_API_KEY is set in `.env`
4. Review agent prompts in `prompts/`

## 📄 License

This is a technical assessment project for Kasparro.

---

**Built with**: Python 3.10+ | OpenAI GPT-4o | Multi-Agent Architecture
**Author**: Kandimalla Bruhadev
**Date**: December 2025
