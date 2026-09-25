# Contributing

Keep model claims tied to recorded evidence. Show failures alongside successes.

For code changes, run Python tests, lint, the frontend build and browser journeys.
For changes to retrieval, prompts, tokenization, models or runtime, also record a live
candidate eval and compare it to the committed baseline.

Do not update expected labels, lower quality bars or overwrite baseline recordings solely
to make a candidate pass. Explain label corrections and model tradeoffs in the change
description. Keep previous model runs when they explain a substantive behavior change.

New eval cases should contain no private supplier information. Document their license,
group related variants together, include expected IDs for every tested destination, and
arrange independent label review when possible.

Treat recordings as model outputs, not hand-editable demo content. Credentials, customer
feeds, model weights, generated databases and local candidate reports must stay out of Git.
