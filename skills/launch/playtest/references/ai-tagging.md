# Tagging free text with AI

Use this when a round has more free-text answers than you want to read and count by hand. The
model does the counting. You keep the codebook and the decision about what to fix.

Contents: When it helps; What the studies found; Steps; Prompt template; Hand check; Personal data.

## When it helps

- Under about 50 comments: read them all yourself (Manalens practice).
- From about 50 comments: an AI model can tag them, and you can still hand-check a sample.
- Above a few hundred: write the codebook from a random sample first, then let the model tag the
  rest. In the CHI 2026 study, two researchers coded a random 200 reviews before GPT-4o coded the
  full set.

## What the studies found

| Task | Result | Study |
|---|---|---|
| Sentiment of 10,000 Steam reviews | GPT-4o-mini 93%, Gemini 2.0 Flash 94% accuracy; both weaker on judging helpfulness | Hamner and Brinkenstråhle Dahlin, 2025 |
| Aspect-based sentiment | LLM agreement with humans near a kappa of 0.55; two humans reached 0.76 | Krause, Otterbach and Singer, 2024 |
| Coding with a human-written codebook | GPT-4o reliability comparable to a human coder | Dutta and others, CHI 2026 |
| Quotes given for each code | All 558 quotes found in the source reviews; 95.2% of code and quote pairs judged accurate; errors mostly from vague comments | Yang and Xiao, 2026 |
| 27 annotation tasks, 11 datasets, GPT-4 | Results depend on the dataset and the task; validate against human labels | Pangakis, Wolken and Fasching, 2023 |

So: AI is good at counting broad themes and sentiment, and less reliable on fine judgments.
Sources and dates: [sources.md](sources.md).

## Steps

1. Export comments with the build number and the tester ID, not names or emails.
2. Read 30 to 50 comments yourself and write 8 to 12 codes, one line of definition each, plus
   `other` so the model does not force a fit (Manalens practice). Examples: `controls`,
   `difficulty_spike`, `unclear_goal`, `performance`.
3. Paste the codebook and the comments into the prompt below.
4. Ask for a table of codes with counts and two quotes each.
5. Hand-check before you trust the counts (next section).
6. Treat a code backed by only one or two quotes as a lead to check in the next round, not a
   finding (Manalens practice).
7. Keep the codebook and the prompt the same between rounds, so builds compare. Use the same
   codebook for Steam reviews after launch, to see whether a playtest theme comes back.

## Prompt template

Asking for exact quotes, and telling the model to drop a claim it cannot quote, follows
Anthropic's advice on reducing hallucinations.

```
You are coding playtest comments. Use only the codes below.
<codebook>
controls: the player struggles with input or camera
difficulty_spike: one part is much harder than what came before
unclear_goal: the player does not know what to do next
performance: frame rate, loading or crashes
other: none of the codes above fits
</codebook>
<comments>
(paste rows of tester_id, build, comment)
</comments>
1. For each comment, give tester_id, the codes that apply and the exact
   words that support each code. If no code fits, use other.
2. Then give a table: code, count, two example quotes.
If you cannot find a supporting quote for a code, do not use the code.
```

## Hand check

Manalens practice, after Pangakis and colleagues:

1. Tag 50 comments yourself with the codebook.
2. Give the model the same 50 comments and the same codebook.
3. Read every comment where you and the model disagree.
4. Fix the code definition that caused each disagreement, then tag the rest.
5. Repeat the check when you change the codebook or the model.
6. Search for each quote the model gives in the export. Drop any code whose quote you cannot find.

## Personal data

Remove names, email addresses and Steam profile links before any upload. The European Commission
counts them as personal data, and pseudonymised data that can be re-identified still counts. Keep
the tester ID map in your own sheet, so you can still join comments to play data.

Join tags to play data where you can: if many testers tag `difficulty_spike` on level 3, check
whether completion drops there before you change the level (Manalens practice).
