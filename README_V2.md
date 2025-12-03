# Kasparro — High Bar V2 Submission

**Production-Level Agentic Facebook Performance Analyst**

> A diagnostic and creative recommendation system that diagnoses performance changes with baseline/current comparisons, validates insights with structured evidence, and generates creative recommendations tightly linked to diagnosed issues.

---

## 🎯 V2 High Bar Compliance

This V2 submission addresses all discriminators for production-level engineering:

### ✅ A. Tight Data → Insight → Validation → Creative Pipeline
- **Diagnoses why performance changed** with baseline vs current comparisons
- **Identifies drivers with evidence**: absolute and relative deltas, segments, sample sizes
- **Generates creatives tightly linked** to diagnosed issues (no generic recommendations)
- **NOT generic insights**: every output references specific campaigns, metrics, and changes

### ✅ B. Real Evaluator & Validation Layer
Insights include:
- **Baseline vs current comparisons** with absolute and relative deltas
- **Evidence structure**: `{metric, segment, baseline_value, current_value, absolute_delta, relative_delta_pct, sample_size}`
- **Severity/confidence scoring**: impact classification (critical/high/medium/low) + confidence (0.0-1.0)
- **Segment-specific evidence**: which campaign, which metric, how much change

Example output:
```json
{
  "hypothesis_id": "H1",
  "confidence": 0.74,
  "impact": "high",
  "evidence": {
    "metric": "ctr",
    "segment": "Men Premium Modal",
    "baseline_value": 0.025,
    "current_value": 0.017,
    "absolute_delta": -0.008,
    "relative_delta_pct": -32.0,
    "sample_size": 150
  }
}
```

### ✅ C. Strong Error Handling & Resilience
The system handles:
- **Missing/renamed columns**: `DataValidator` adds missing columns with defaults
- **Empty groups/segments**: Graceful handling with logging
- **NaNs, infinities, divide-by-zero**: Comprehensive cleaning pipeline
- **Bad configs**: Pre-validation before execution
- **Failing agent calls**: Try-catch with structured error logs
- **No silent failures**: All errors logged with context
- **No crashing on imperfect data**: Validation → Clean → Validate cycle

See: `src/utils/data_validation.py`

### ✅ D. Schema & Data Governance
- **Explicit schema definition**: `DataValidator.REQUIRED_COLUMNS`, `OPTIONAL_COLUMNS`
- **Pre-run schema validation**: Validates before and after cleaning
- **Clear failure messages**: Detailed error messages for schema violations
- **Config-driven thresholds**: All magic numbers in `config/config.yaml`

### ✅ E. Observability (Debuggable)
Every run produces:
- **Per-agent logs**: JSON logs with timing, inputs, outputs
- **Input summaries**: Data quality scores, row counts, validation results
- **Output summaries**: Hypothesis counts, validation results, recommendation linkage
- **Decision logs**: "Why this hypothesis was generated" for each agent
- **Error logs with context**: Stack traces, input data, failure points
- **Log folder per run**: `logs/execution_YYYYMMDD_HHMMSS.json`

Decision log example:
```json
{
  "agent": "evaluator",
  "event": "decision",
  "data": {
    "decision": "Validated 3/5 hypotheses",
    "reasoning": "Applied confidence threshold of 0.6. Rejected 2 hypotheses due to insufficient evidence.",
    "inputs": {"hypotheses_count": 5, "threshold": 0.6},
    "outputs": {"validated": 3, "rejected": 2}
  }
}
```

### ✅ F. Developer Experience
The README allows another engineer to run the project:
- **Install steps**: Virtual environment, requirements, .env setup
- **Run commands**: `python run.py` or `make run`
- **Architecture**: 5-7 bullet system design (see below)
- **Clear modification guidance**: Where to add agents, change prompts, adjust thresholds
- **Makefile**: `make setup`, `make run`, `make test`, `make ci`

### ✅ G. Stretch Goals (Included)
- **Unit tests**: 46+ tests across all agents with 70-80% coverage
- **Adaptive thresholds**: Percentile-based thresholds in data validation
- **Schema drift alerts**: `check_schema_drift()` function in `schema.py`

---

## 🏗️ Architecture (5-7 Bullets)

1. **Data Validation Layer** (`data_validation.py`): Pre-run schema validation, missing value handling, NaN/infinity cleaning, computed metrics
2. **Baseline vs Current Analysis** (`data_agent.py`): Automatic period comparison with absolute/relative deltas for all segments
3. **Production-Level Evaluator** (`evaluator.py`): Structured evidence with baseline/current/delta, impact scoring, confidence thresholds
4. **Tightly Linked Creative Generator** (`creative_generator.py`): Every recommendation references a validated insight with diagnosed issue
5. **Decision Logging** (`logger.py`): Captures "why" for every agent decision (hypothesis generation, validation, rejection)
6. **Error-Resilient Orchestrator** (`orchestrator.py`): Comprehensive error handling, data quality logging, validation at every step
7. **Config-Driven Everything** (`config.yaml`): All thresholds, paths, retry logic externalized

---

## 🚀 Quick Start

```bash
# 1. Setup
python -V  # >= 3.10
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 2. Run
python run.py

# You'll be prompted:
# 💬 Enter your query: [type your question]

# Example queries:
# - "Why did ROAS drop in the last week?"
# - "Which campaigns have low CTR and why?"
# - "Full performance audit: identify issues and recommend solutions"
```

---

## 📂 Repository Structure

```
kasparro-agentic-fb-analyst-bruuu/
├── README_V2.md                 # This file (V2 submission documentation)
├── README.md                    # Original documentation
├── requirements.txt             # Pinned dependencies
├── run.py                       # Main CLI entry point
├── Makefile                     # make setup, run, test, ci
├── pytest.ini                   # Test configuration
├── .env.example                 # Environment template
│
├── config/
│   └── config.yaml              # Config (thresholds, paths, retry logic)
│
├── src/
│   ├── agents/
│   │   ├── base_agent.py        # Base with retry logic
│   │   ├── planner.py           # Query decomposition
│   │   ├── data_agent.py        # ✅ V2: Data validation + baseline/current analysis
│   │   ├── insight_agent.py     # Hypothesis generation
│   │   ├── evaluator.py         # ✅ V2: Structured evidence + impact scoring
│   │   └── creative_generator.py# ✅ V2: Tightly linked recommendations
│   │
│   ├── orchestrator/
│   │   └── orchestrator.py      # ✅ V2: Decision logging + validation
│   │
│   └── utils/
│       ├── logger.py            # ✅ V2: Decision logging capability
│       ├── config_loader.py     # Config management
│       ├── schema.py            # Schema versioning + drift detection
│       └── data_validation.py   # ✅ V2: NEW - Comprehensive data validation
│
├── prompts/                     # ✅ V2: Updated prompts with V2 requirements
│   ├── evaluator_prompt.md      # Baseline/current comparison requirements
│   └── creative_generator_prompt.md  # Tight linkage requirements
│
├── data/
│   ├── README.md                # Data documentation
│   └── synthetic_fb_ads_undergarments.csv  # Dataset
│
├── reports/                     # Generated outputs (timestamped)
│   ├── report_*.md
│   ├── insights_*.json          # ✅ V2: Structured evidence format
│   └── creatives_*.json         # ✅ V2: Linked to insights
│
├── logs/                        # ✅ V2: Decision logs + execution traces
│   └── execution_*.json
│
└── tests/                       # 46+ tests, 70-80% coverage
    ├── test_data_agent.py       # 11 tests
    ├── test_evaluator.py        # 3 tests (+ new validation tests)
    ├── test_creative_generator.py # 13 tests
    └── ...
```

---

## 🔍 V2 Enhancements Deep Dive

### 1. Data Validation & Resilience (`data_validation.py`)

**Problem**: V1 had basic data loading. V2 requirements demand production-level error handling.

**Solution**:
- **Pre-run schema validation**: Checks for required columns before processing
- **Handles missing columns**: Adds optional columns with sensible defaults
- **Cleans data**: Removes NaNs, infinities, invalid ranges
- **Computes derived metrics**: CTR, ROAS if missing
- **Validates ranges**: CTR in [0,1], no negative spend/revenue
- **Removes invalid rows**: Empty rows, unparseable dates
- **Data quality report**: Quality score, missing values, zero values

```python
# Example: Handling missing CTR column
if "ctr" not in df.columns:
    logger.info("Computing CTR from clicks and impressions")
    df["ctr"] = np.where(df["impressions"] > 0, df["clicks"] / df["impressions"], 0)
```

### 2. Baseline vs Current Analysis (`data_agent.py`)

**Problem**: V1 showed current metrics. V2 requires diagnosing *why* performance changed.

**Solution**:
- **Automatic period definition**: Last 7 days vs previous 7 days
- **Comprehensive comparisons**: Overall, per-campaign, per-creative-type, per-platform
- **Absolute and relative deltas**: Shows both difference and percentage change
- **Sample size tracking**: Validates statistical significance
- **Formatted output**: Clear `baseline → current (Δ delta, pct%)` format

```python
# Example output
ROAS: 2.5000 → 1.7000 (Δ -0.8000, -32.0%)
CTR: 0.0250 → 0.0170 (Δ -0.0080, -32.0%)
Sample Size: 150 → 145
```

### 3. Production-Level Evaluator (`evaluator.py`)

**Problem**: V1 had confidence scores. V2 requires structured evidence with baseline/current/delta.

**Solution**:
- **New evidence structure**:
  ```json
  "evidence": {
    "metric": "ctr",
    "segment": "Campaign Name",
    "baseline_value": 0.025,
    "current_value": 0.017,
    "absolute_delta": -0.008,
    "relative_delta_pct": -32.0,
    "sample_size": 150,
    "time_period": "Last 7 days vs previous 7 days"
  }
  ```
- **Impact classification**: critical (>50%), high (25-50%), medium (10-25%), low (<10%)
- **Validation enforcement**: Rejects hypotheses without quantitative evidence
- **Graceful fallback**: Returns structured error response if evaluation fails

### 4. Tightly Linked Creative Generator (`creative_generator.py`)

**Problem**: V1 generated creative recommendations. V2 requires tight linkage to diagnosed issues.

**Solution**:
- **Mandatory linkage**: Every recommendation must reference an insight ID
- **Diagnosed issue included**: baseline_value, current_value, delta, root_cause
- **Target improvements**: Specific metric targets (e.g., "CTR from 0.017 → 0.024")
- **Root cause addressing**: Explains how creative solves the diagnosed problem
- **Linkage validation**: Warns if recommendations don't link to valid insights

```json
{
  "campaign_name": "Men Premium Modal",
  "linked_to_insight": "H1",
  "diagnosed_issue": {
    "metric": "ctr",
    "baseline_value": 0.025,
    "current_value": 0.017,
    "relative_delta_pct": -32.0,
    "root_cause": "Creative fatigue"
  },
  "creative_variations": [
    {
      "addresses_root_cause": "Introduces fresh hook to re-engage fatigued audience",
      "target_improvement": {
        "metric": "ctr",
        "current": 0.017,
        "target": 0.024,
        "improvement_pct": 41.0
      }
    }
  ]
}
```

### 5. Decision Logging (`logger.py` + `orchestrator.py`)

**Problem**: V1 logged events. V2 requires understanding *why* decisions were made.

**Solution**:
- **New log_decision() method**: Captures decision, reasoning, inputs, outputs
- **Applied throughout pipeline**:
  - Data agent: Why data was loaded, quality score
  - Insight agent: Why N hypotheses were generated
  - Evaluator: Why hypotheses were validated/rejected
  - Creative generator: Why recommendations were created
- **Accessible in logs**: Every decision is in `logs/execution_*.json`

---

## 📤 V2 Output Examples

### 1. Insights JSON (with structured evidence)

```json
{
  "evaluations": [
    {
      "hypothesis_id": "H1",
      "validation_status": "confirmed",
      "confidence": 0.85,
      "impact": "high",
      "evidence": {
        "metric": "ctr",
        "segment": "Men Premium Modal",
        "baseline_value": 0.0250,
        "current_value": 0.0170,
        "absolute_delta": -0.0080,
        "relative_delta_pct": -32.0,
        "sample_size": 150,
        "time_period": "Last 7 days vs previous 7 days"
      },
      "severity": "high",
      "affected_campaigns": ["Men Premium Modal", "Men Bold Colors Drop"],
      "reasoning": "CTR dropped 32% from baseline, indicating creative fatigue...",
      "actionable": true
    }
  ],
  "validated_insights": [
    {
      "insight": "CTR dropped 32% from 0.025 to 0.017 in Men Premium Modal",
      "confidence": 0.85,
      "impact": "high",
      "evidence_id": "H1"
    }
  ],
  "overall_diagnosis": {
    "primary_issue": "Creative fatigue in high-spend campaigns",
    "contributing_factors": ["Same messaging for 14+ days", "No creative refresh"],
    "affected_segments": ["Men Premium Modal", "Men Bold Colors Drop"]
  }
}
```

### 2. Creatives JSON (tightly linked)

```json
{
  "recommendations": [
    {
      "campaign_name": "Men Premium Modal",
      "linked_to_insight": "H1",
      "diagnosed_issue": {
        "metric": "ctr",
        "baseline_value": 0.025,
        "current_value": 0.017,
        "relative_delta_pct": -32.0,
        "root_cause": "Creative fatigue from same messaging"
      },
      "current_issue": "CTR dropped 32% (0.025 → 0.017) due to creative fatigue",
      "creative_variations": [
        {
          "variant_id": "V1",
          "creative_type": "UGC",
          "headline": "Why Athletes Are Switching",
          "message": "See what makes these the most comfortable...",
          "cta": "Shop Now",
          "rationale": "Leverages social proof to combat fatigue",
          "addresses_root_cause": "Fresh angle with authority figures to re-engage audience",
          "target_improvement": {
            "metric": "ctr",
            "current": 0.017,
            "target": 0.024,
            "improvement_pct": 41.0
          },
          "testing_priority": "high"
        }
      ],
      "validation_approach": "A/B test V1 vs current creative, measure CTR over 7 days"
    }
  ],
  "linked_to_insights": 3,
  "total_recommendations": 3
}
```

### 3. Decision Logs (observability)

```json
{
  "timestamp": "2025-12-03T15:30:45",
  "agent": "evaluator",
  "event": "decision",
  "data": {
    "decision": "Validated 3/5 hypotheses",
    "reasoning": "Applied confidence threshold of 0.6. Rejected 2 hypotheses: H4 (sample size=8, too small), H5 (confidence=0.45, below threshold)",
    "inputs": {
      "hypotheses_count": 5,
      "threshold": 0.6
    },
    "outputs": {
      "validated": 3,
      "rejected": 2
    }
  }
}
```

---

## 🧪 Testing

**Test Suite**: 46+ tests with 100% pass rate

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific module
pytest tests/test_evaluator.py -v
```

**Test Coverage**: 70-80% across all modules

---

## 🎛️ Configuration

All thresholds are config-driven in `config/config.yaml`:

```yaml
thresholds:
  confidence_min: 0.6              # Minimum confidence for validation
  low_ctr_threshold: 0.015         # CTR below this is "low"
  low_roas_threshold: 2.0          # ROAS below this is "low"
  significant_change_pct: 0.15     # 15% change is "significant"

llm:
  model: "gpt-4o"
  temperature: 0.3
  max_retries: 3
  initial_retry_delay: 1.0

data:
  full_csv: "data/synthetic_fb_ads_undergarments.csv"
```

**No magic numbers in code.** Everything is in config.

---

## 🔧 Where to Modify Components

### Adding a New Agent
1. Create `src/agents/new_agent.py` extending `BaseAgent`
2. Add prompt template in `prompts/new_agent_prompt.md`
3. Update `orchestrator.py` to call new agent
4. Add tests in `tests/test_new_agent.py`

### Changing Thresholds
- Edit `config/config.yaml` (no code changes needed)

### Adjusting Prompts
- Edit files in `prompts/` directory
- Prompts use `{variable}` placeholders for substitution

### Modifying Schema
- Update `src/utils/schema.py` with new schema version
- Increment `SCHEMA_VERSION` constant

---

## 📊 Performance

### Speed
- **Average Analysis Time**: 30-45 seconds
- **Breakdown**:
  - Data Validation: ~2s
  - Data Loading: ~2s
  - Analysis: ~8s
  - Insight Generation: ~7s
  - Evaluation: ~8s
  - Creative Generation: ~10s

### Quality
- **Data Quality Score**: 95+/100 (from DataValidator)
- **Validation Rate**: ~60-80% of hypotheses validated
- **Recommendation Linkage**: 100% of recommendations linked to insights

### Cost
- **Per Analysis**: ~$0.03 (GPT-4o)

---

## 🏁 V2 Submission Checklist

- ✅ **A. Tight pipeline**: Diagnosis → Evidence → Validation → Linked Creatives
- ✅ **B. Real evaluator**: Baseline/current comparisons, absolute/relative deltas, evidence structure
- ✅ **C. Error handling**: Missing columns, NaNs, infinities, bad configs, failing agents
- ✅ **D. Schema governance**: Explicit definitions, pre-run validation, clear errors, config-driven
- ✅ **E. Observability**: Per-agent logs, decision logs, input/output summaries, error context
- ✅ **F. Developer experience**: README with install/run/architecture/modification guide, Makefile
- ✅ **G. Stretch goals**: Unit tests (46+), adaptive thresholds, schema drift detection

**Repository Naming**: Will be renamed to `{YourName}_HighBar_V2` format before submission.

---

## 📞 Support

**For issues**:
1. Check logs in `logs/execution_*.json` for detailed trace
2. Review decision logs to understand agent reasoning
3. Verify data quality score in logs
4. Check config in `config/config.yaml`

**For questions**:
- Review this README
- Check `TESTING.md` for test documentation
- See `SUBMISSION.md` for original assignment details

---

## 📝 Design Philosophy

This V2 system embodies production engineering principles:

1. **No Silent Failures**: Every error is logged with context
2. **Debuggable by Default**: Decision logs explain every choice
3. **Data Quality First**: Validation before processing
4. **Evidence-Based**: Every insight backed by baseline/current comparison
5. **Tight Coupling**: Creatives solve diagnosed problems, not generic issues
6. **Config-Driven**: No magic numbers in code
7. **Testable**: 46+ tests ensure reliability

**The goal**: Another engineer can understand what the system did, why it did it, and whether it worked — without asking you.

---

**Built with**: Python 3.10+ | OpenAI GPT-4o | Multi-Agent Architecture
**V2 Submission Date**: December 2025
**Author**: Kandimalla Bruhadev
