# Writing the reading edition

Apply ASD-STE100 where it fits this descriptive summary. Use one main topic per sentence, active voice when the actor is known, and consistent terms. Use familiar words with clear meanings; retain necessary technical names and explain them at first use. Keep most descriptive sentences under 25 words, but vary their length: a run of short sentences reads as badly as a run of long ones. Split a long sentence only where its conditions and qualifications survive the split. Use short paragraphs, and lists only for parallel information. Full compliance also requires the standard's controlled vocabulary and other rules; this workflow does not certify compliance.

Reference: [ASD's official FAQ](https://www.asd-ste100.org/STE_faq.html) and [Issue 9, word-count guidance](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf).

For this reader, preserve exact names, identifiers, quantities, units, dates, negation, and differences between must, should, may, and proposed. Keep original text and direct quotations verbatim. Do not invent an actor to force active voice. Introduce an abbreviation only if it helps later reading. Replace dense chains of technical nouns with a plain explanation of the relationship.

## Write like a person

Simple English must still read as if a person wrote it. Before rendering, run a humanizer pass over every generated string: TL;DR, theme descriptions, gists, section text, examples, takeaways, questions, and the coverage note. Read [the humanizer guide](humanizer.md) and follow its embedded mode: mark the tells, rewrite, check the draft, and write only the final text into the JSON. Use its neutral voice for reference text. Leave original text, quotes, names, identifiers, numbers, and dates unchanged. These checks matter most for a reading edition:

- State points directly. Cut "X, not Y" contrasts unless the negative half corrects something a reader would otherwise believe. Write "The backlog has 40 unscheduled issues" rather than "The backlog is a wish list, not a plan."
- Attribute where it matters, for claims, estimates, and judgments. A section about the document's plan does not need "the brief says" in every sentence.
- Vary sentence openings and length. Merge a run of short sentences that share a subject.
- Write list items as plain sentences, without a label and colon on every item.
- No one-line closers, staged lead-ins ("The last problem matters most"), dashes, or triads added for rhythm.
- A takeaway adds a conclusion. It does not restate the gist.

## Examples that explain

Put an example immediately after the difficult concept. Prefer a small scenario with a condition, action, and consequence. Use the document's domain and keep the example short. Define the concept first; an analogy alone is not a definition. Do not add an example to every paragraph or repeat one that is already clear.

Use the renderer's example block. Select `origin: "source"` only when the source actually supplies the scenario; paraphrase faithfully and link its passage. Use `origin: "illustration"` for an invented teaching scenario grounded in a source concept. The renderer labels these differently. Hypothetical outcomes illustrate the stated rule, not observed product behavior. Do not invent service guarantees, thresholds, owners, or commitments. If the source is too ambiguous to support an example, explain the ambiguity or add a follow-up question instead.

Review the example against its linked source: does it preserve prerequisites, failure conditions, and the difference between current and proposed behavior? Keep source links outside the example's factual claims when they support only its underlying concept.
