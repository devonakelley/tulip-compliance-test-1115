# Debug Guide: Zero Gaps Found Issue

## ✅ Debug Logging Added

I've added debug logging to show the actual similarity scores when running gap analysis.

---

## How to Use This Debug Info

### Step 1: Run Gap Analysis

1. Go to your application
2. Navigate to Tab 3 (Gap Analysis)
3. Click "Run Gap Analysis"

### Step 2: Check Backend Logs

Run this command to see the debug output:

```bash
tail -f /var/log/supervisor/backend.out.log | grep "DEBUG"
```

Or view recent logs:

```bash
tail -n 100 /var/log/supervisor/backend.out.log | grep "🔍"
```

### Step 3: Look for These Lines

You'll see output like this for each regulatory clause:

```
🔍 DEBUG - Clause 5.1 top 5 similarity scores:
  #1: 0.682 - QSP 9.1-3 | 5.2.1
  #2: 0.651 - QSP 9.1-4 | 3.1
  #3: 0.589 - QSP 9.1-1 | 7.3
  #4: 0.544 - QSP 7.3-3 | 2.1
  #5: 0.501 - QSP 9.1-6 | 4.2
  Current threshold: 0.75 | Matches above threshold: 0
```

---

## Diagnosis Guide

### Scenario 1: Scores are 0.65-0.74 ✅ COMMON
**Example:**
```
  #1: 0.712 - QSP 7.3-3 | Risk Management
  #2: 0.689 - QSP 9.1-3 | Technical Documentation
  Current threshold: 0.75 | Matches above threshold: 0
```

**Diagnosis:** Threshold (0.75) is too high. Your QSPs DO match but just below the threshold.

**Fix:** Lower the threshold to 0.65 or 0.70

**How to fix:**
1. Edit `/app/backend/core/change_impact_service_mongo.py`
2. Find line 34: `self.impact_threshold = 0.75`
3. Change to: `self.impact_threshold = 0.70`  (or 0.65)
4. Restart backend: `sudo supervisorctl restart backend`
5. Run gap analysis again

**Recommended threshold:**
- If highest score is 0.70-0.74 → use threshold 0.68
- If highest score is 0.65-0.69 → use threshold 0.63
- If highest score is 0.60-0.64 → use threshold 0.58

---

### Scenario 2: Scores are 0.45-0.59 ⚠️ MODERATE
**Example:**
```
  #1: 0.543 - QSP 9.1-1 | Overview
  #2: 0.521 - QSP 9.1-6 | General
  Current threshold: 0.75 | Matches above threshold: 0
```

**Diagnosis:** Weak semantic similarity. Your QSPs may not be directly related to the regulatory changes.

**Possible causes:**
1. You uploaded a general overview QSP instead of specific technical QSPs
2. The regulatory changes are about topics not covered in your QSPs
3. The diff generated deltas for clauses your QSPs don't address

**Fix options:**

**Option A:** Lower threshold to catch weak matches (may bring back false positives)
```python
self.impact_threshold = 0.50  # Very permissive
```

**Option B:** Check what you uploaded
- Are your QSPs about risk management (ISO 14971)?
- Did you upload the right regulatory documents?
- Did the diff generate relevant deltas?

**Option C:** Upload more specific QSPs
- Instead of "9.1-1 Overview", upload "7.3-3 Risk Management"
- Upload QSPs that actually implement the regulatory requirements

---

### Scenario 3: Scores are 0.30-0.44 ❌ LOW
**Example:**
```
  #1: 0.387 - QSP 9.1-1 | Document Overview
  #2: 0.362 - QSP 4.2-1 | Document Control
  Current threshold: 0.75 | Matches above threshold: 0
```

**Diagnosis:** Your QSPs don't relate to the regulatory changes at all.

**Likely issues:**
1. **Wrong regulatory standard:** You uploaded ISO 14971 but your QSPs are about ISO 13485
2. **Wrong diff:** The diff is comparing wrong versions or wrong standards
3. **Generic QSPs:** Your QSPs are too high-level and don't contain specific technical content

**How to check:**
1. What regulatory documents did you upload?
   - Check Tab 1: Should show "ISO 14971:2019" and "ISO 14971:2020"
2. What deltas were generated?
   - Check backend logs for: "Analyzing delta: ISO 14971:2020 Clause X"
3. What QSPs did you upload?
   - Check Tab 2: Should show specific QSPs like "7.3-3 Risk Management"

**Fix:** Upload the correct documents or accept that your QSPs don't address these regulatory changes.

---

### Scenario 4: Scores are 0.80+ but still 0 matches 🐛 BUG
**Example:**
```
  #1: 0.843 - QSP 7.3-3 | Risk Management
  #2: 0.812 - QSP 9.1-3 | Technical Docs
  Current threshold: 0.75 | Matches above threshold: 0
```

**Diagnosis:** This is a bug. Scores are above threshold but not being matched.

**Possible cause:** The `similarities` array is not being populated correctly.

**Fix:** Report this as a bug. There's an issue in the matching logic.

---

### Scenario 5: No debug logs appear at all 🚨 CRITICAL
**Symptom:** You don't see any "🔍 DEBUG" lines in the logs

**Possible causes:**
1. Gap analysis isn't actually running
2. No deltas were generated (diff is empty)
3. Backend didn't restart properly
4. No QSP sections are loaded

**How to debug:**

Check if QSPs are loaded:
```bash
tail -n 100 /var/log/supervisor/backend.out.log | grep "Using.*QSP sections"
```

Should see: `Using 50 QSP sections for impact analysis` (or similar)

If you see: `Using 0 QSP sections` → Problem is with QSP upload/mapping

Check if deltas exist:
```bash
tail -n 100 /var/log/supervisor/backend.out.log | grep "Analyzing delta"
```

Should see: `Analyzing delta: ISO 14971:2020 Clause 5.1`

If you don't see this → Problem is with diff generation (Tab 1)

---

## Quick Fix Matrix

| Highest Score | Recommended Threshold | Expected Results |
|--------------|----------------------|------------------|
| 0.72-0.80 | 0.68 | 3-5 matches, good precision |
| 0.65-0.71 | 0.63 | 3-7 matches, moderate precision |
| 0.58-0.64 | 0.55 | 5-10 matches, lower precision |
| 0.45-0.57 | 0.50 | 8-12 matches, many false positives |
| Below 0.45 | Don't lower threshold | QSPs don't relate to regulatory changes |

---

## Adaptive Threshold Strategy (Recommended)

Instead of a fixed threshold, you could use an adaptive approach:

**Strategy:** Always return the top 3 matches even if below threshold, but mark them differently.

**How to implement:**
1. Keep threshold at 0.75 for "high confidence" matches
2. If 0 matches above 0.75, return top 3 matches anyway
3. Mark these as "low confidence" in the UI

**Edit the code:**
```python
# After sorting similarities
if len(similarities) == 0 and len(all_scores) > 0:
    # No matches above threshold, return top 3 anyway
    logger.warning(f"No matches above threshold {self.impact_threshold}, returning top 3 as low-confidence")
    top_scores = all_scores[:3]
    for score, doc, section in top_scores:
        # Find the full QSP object
        for qsp in qsp_sections:
            if qsp['doc_name'] == doc and qsp.get('section_path', '') == section:
                similarities.append((score, qsp))
                break
```

This ensures you always get SOME results, but users know they're lower confidence.

---

## Most Likely Diagnosis

Based on the jump from 0.55 → 0.75 threshold causing 15 matches → 0 matches:

**My prediction:** Your scores are probably in the **0.60-0.72 range**.

The old 0.55 threshold caught everything (including false positives).
The new 0.75 threshold is too strict.
**The sweet spot is probably 0.65-0.68.**

---

## Next Steps

1. **Run gap analysis** with the debug logging enabled
2. **Share the debug output** (the "🔍 DEBUG" lines)
3. **I'll tell you the exact threshold to use**

Example of what to share:
```
🔍 DEBUG - Clause 5.1 top 5 similarity scores:
  #1: 0.682 - QSP 9.1-3 | 5.2.1
  #2: 0.651 - QSP 9.1-4 | 3.1
  #3: 0.589 - QSP 9.1-1 | 7.3
  Current threshold: 0.75 | Matches above threshold: 0

🔍 DEBUG - Clause 7.4 top 5 similarity scores:
  #1: 0.711 - QSP 8.2-1 | 3.2
  #2: 0.698 - QSP 7.3-3 | 5.1
  #3: 0.654 - QSP 9.1-3 | 6.1
  Current threshold: 0.75 | Matches above threshold: 0
```

Based on this, I'd recommend: **Use threshold 0.68** (catches the 0.71 match but not the noise)

---

## Emergency Temporary Fix

If you need results RIGHT NOW for a demo:

```python
# Line 34 in change_impact_service_mongo.py
self.impact_threshold = 0.55  # Revert to original

# This will restore the old behavior (15 matches)
# Use only temporarily while we tune the threshold properly
```

---

**Status:** Debug logging added ✅
**Next:** Run gap analysis and share the debug output
**ETA to fix:** 5 minutes once we see the scores
