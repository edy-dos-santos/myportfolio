# Analysis plan

This plan is written before the real study. Keep it with the data.

## Research questions

1. Does story-first (B) reduce effort without hurting accuracy?
2. Who prefers which chat, and why?

## Metrics

Definitions and column names match `ab_results.csv` from the simulated pilot. One exception: time on task is measured by `chat_variant.py` from the participant's own reading and typing time (the `ms` values in the session file), not modelled from word counts.

In the real data, `est_customer_seconds` holds measured time (participant `ms` from `chat_variant.py`, from the moment the chat prompt appears). `time_source` is `measured`. In the simulated data it is a model from word counts, and `time_source` is `modelled`. Never compare or average the two. In Power BI, filter on `data_source` and `time_source`.

| Metric | Column | Definition | Role |
|---|---|---|---|
| Task success | `task_success` | 1 if the claim was lodged with all key facts correct. Same rule as the pilot. | Primary |
| Ease (SEQ) | `seq` | 1 to 7, from the post-task questionnaire | Primary |
| Time on task | `est_customer_seconds` | Participant time in seconds, from the session file | Secondary |
| Questions asked | `questions_asked` | Question sentences in Sam's turns | Secondary |
| Repeat questions | `reasked_facts` | Questions about a fact the participant had already given. Score by hand from the transcript, using the same rule as the judge in the pilot | Secondary |
| Satisfaction (CSAT) | `csat` | 1 to 5, from the post-task questionnaire | Secondary |
| Preference | `preferred_variant` | A, B or none, from Part B question 1 | Secondary |

Facts correct (`facts_correct`, `facts_correct_pct`) is checked against the claim input, as in the pilot. Record it as a check, not as a main result.

## Analysis

With 8 to 10 people, the tests are exploratory. Say so in every write-up.

- Descriptives per variant: median and interquartile range (IQR) for seq, csat, time and questions. Count and percentage for task success and preference.
- Paired differences: B minus A for each participant, for seq and time. Report the median difference and the IQR.
- Tests: Wilcoxon signed-rank test for seq and time. Sign test for preference (ignore "none").
- Qualitative: code the comments and the moderator notes into themes. Use one code per point. Keep the quotes with the code. Two people code a subset (at least three sessions) and compare.
- Think-aloud notes: tag each "repeat", "confusion", "slow", "praise" or "error". Count the tags per variant.

## Decision rule

Use the same rule as the simulated pilot (`metrics.py`, `recommend`):

1. If task success differs by 2 or more participants, recommend the higher.
2. Else, if mean time differs by 15% or more (against the slower variant), and the faster variant's mean CSAT is not lower by more than 0.5, recommend the faster.
3. Else, if one variant is preferred by at least 7 of 10 participants, recommend it.
4. Else: no clear winner. Keep the current design (B) and let the study decide.

With fewer than 6 complete pairs, make no recommendation.

## Loading the data in Power BI

1. Save the real data as `results/real/*.json` (one file per session). Export them to a single CSV with the columns in `data-template.csv`. Fill `card` and `moderator_notes` by hand.
2. In Power BI Desktop, choose Get data, then Text/CSV. Choose `data-template.csv`. Check the file is read as UTF-8.
3. Choose Get data, then Text/CSV again, for `ab_results.csv` from the simulated pilot (`results/simulated/`).
4. In Power Query, add a column `source` with the value "real" for the real data and "simulated" for the pilot. Append the two queries.
5. Always filter on `data_source` (or `source`) before you build a visual. Do not mix simulated and real results in one chart.
6. Build the visuals: task success by variant, SEQ by variant, time by persona, and preference counts.

## What would change the recommendation

- A large gap in task success on one card. Check the card before you trust the result.
- A repeat-question count that goes the other way from the time result. This means story-first may ask fewer questions but still miss facts.
- Strong comments that a variant felt slow, or a variant missed facts for people with low digital confidence. This would matter more than a small difference in numbers.
- A session that ends at the 10-minute stop, or a handoff to a person. Note each one. Do not count it as a success unless the rule says so.

Portfolio exercise, not legal or ethics advice. Check references against current versions before use.
