---
trigger: manual
---

# Base rules

## Keep Me in the Loop
- Always explain what you're planning to do before you start coding.
- After each change, briefly describe what was done.
- Ask for feedback before continuing to the next step.

## Incremental Development
- Build features in small, testable steps.
- Do not attempt large-scale changes all at once.
- Prioritize clarity and stability over speed.

## Test Everything
- For each change, include unit tests or integration tests where applicable.
- Use mocks or stubs if external systems are involved.
- Confirm the code compiles (or runs) and passes existing tests before continuing.

## Add Logging
- Add clear and descriptive logs to all major actions or decision points.
- Prefer structured logging if available (e.g., JSON format for backend).
- Avoid overly verbose logs; focus on what would help during debugging.