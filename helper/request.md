{Your feature or change request here}

---

**1. Deep Analysis & Research**

* **Clarify Intent**: Review the full user request and any relevant context in conversation or documentation.
* **Gather Context**: Use all available tools (file\_search, code analysis, web search, docs) to locate affected code, configurations, and dependencies.
* **Define Scope**: List modules, services, and systems impacted; identify cross-project boundaries.
* **Formulate Approaches**: Brainstorm possible solutions; evaluate each for feasibility, risk, and alignment with project standards.

**2. Impact & Dependency Assessment**

* **Map Dependencies**: Diagram or list all upstream/downstream components related to the change.
* **Reuse & Consistency**: Seek existing patterns, libraries, or utilities to avoid duplication and maintain uniform conventions.
* **Risk Evaluation**: Identify potential failure modes, performance implications, and security considerations.

**3. Strategy Selection & Autonomous Resolution**

* **Choose an Optimal Path**: Select the approach with the best balance of reliability, maintainability, and minimal disruption.
* **Resolve Ambiguities Independently**: If questions arise, perform targeted tool-driven research; only escalate if blocked by high-risk or missing resources.

**4. Execution & Implementation**

* **Pre-Change Verification**: Read target files and tests fully to avoid side effects.
* **Implement Edits**: Apply code changes or new files using precise, workspace-relative paths.
* **Incremental Commits**: Structure work into logical, testable steps.

**5. Tool-Driven Validation & Autonomous Corrections**

* **Run Automated Tests**: Execute unit, integration, and end-to-end suites; run linters and static analysis.
* **Self-Heal Failures**: Diagnose and fix any failures; rerun until all pass unless prevented by missing permissions or irreversibility.

**6. Verification & Reporting**

* **Comprehensive Testing**: Cover positive, negative, edge, and security cases.
* **Cross-Environment Checks**: Verify behavior across relevant environments (e.g., staging, CI).
* **Result Summary**: Report what changed, how it was tested, key decisions, and outstanding risks or recommendations.

**7. Safety & Approval**

* **Autonomous Changes**: Proceed without confirmation for non-destructive code edits and tests.
* **Escalation Criteria**: If encountering irreversible actions or unresolved conflicts, provide a concise risk-benefit summary and request approval.