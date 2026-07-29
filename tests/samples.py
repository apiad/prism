"""One representative spec per archetype, shared by the test suite and docs."""

from __future__ import annotations

SAMPLES: dict[str, str] = {
    "flow": """
type: flow
title: Ingestion pipeline
steps:
  - {id: ingest, label: Ingest, sublabel: S3 + Kafka, icon: database, accent: 0}
  - {id: verify, label: Verify, sublabel: schema + dedupe, icon: shield-check, accent: 1}
  - {id: publish, label: Publish, sublabel: warehouse, icon: send, accent: 2}
""",
    "hierarchy": """
type: hierarchy
title: System decomposition
root:
  label: Platform
  icon: box
  children:
    - label: API
      icon: server
      children:
        - {label: Auth}
        - {label: Billing}
    - label: Web
      icon: globe
      children:
        - {label: Dashboard}
""",
    "cycle": """
type: cycle
title: Build-measure-learn
center: {label: Kaizen}
steps:
  - {label: Build, icon: hammer, accent: 0}
  - {label: Measure, icon: gauge, accent: 1}
  - {label: Learn, icon: lightbulb, accent: 2}
""",
    "timeline": """
type: timeline
title: Product history
events:
  - {id: seed, when: 2023 Q1, label: Seed, icon: sprout, accent: 0}
  - {id: beta, when: 2023 Q4, label: Private beta, icon: flask-conical, accent: 1}
  - {id: ga, when: 2024 Q2, label: General availability, icon: rocket, accent: 2}
eras:
  - {label: Pre-revenue, span: [seed, beta], accent: 4}
""",
    "pyramid": """
type: pyramid
title: Needs
levels:
  - {label: Self-actualisation}
  - {label: Esteem}
  - {label: Belonging}
  - {label: Safety}
  - {label: Physiological}
""",
    "stack": """
type: stack
title: Platform tiers
layers:
  - {label: Application, sublabel: product surfaces, side: L7}
  - {label: Services, sublabel: domain APIs, side: L5}
  - {label: Data, sublabel: warehouse + lake, side: L3}
  - {label: Infrastructure, sublabel: compute + network, side: L1}
""",
    "comparison": """
type: comparison
title: Build versus buy
criteria: [Time to value, Ongoing cost, Control]
columns:
  - header: {label: Build, icon: hammer}
    items:
      - {label: 6-9 months}
      - {label: Engineering time}
      - {label: Total}
  - header: {label: Buy, icon: shopping-cart}
    items:
      - {label: 2 weeks}
      - {label: Subscription}
      - {label: Vendor roadmap}
""",
    "quadrant": """
type: quadrant
title: Effort versus impact
axes:
  x: {label: Effort, low: Low, high: High}
  y: {label: Impact, low: Low, high: High}
quadrant_labels: [Quick wins, Big bets, Fill-ins, Thankless]
items:
  - {label: Search rewrite, x: 0.8, y: 0.85}
  - {label: Dark mode, x: 0.2, y: 0.7}
  - {label: Log cleanup, x: 0.25, y: 0.2}
  - {label: Legacy migration, x: 0.85, y: 0.25}
""",
    "hub": """
type: hub
title: Shared platform
center: {label: Core platform, icon: box}
spokes:
  - {label: Payments, icon: credit-card, accent: 0}
  - {label: Identity, icon: key-round, accent: 1}
  - {label: Search, icon: search, accent: 2}
  - {label: Messaging, icon: message-circle, accent: 3}
  - {label: Analytics, icon: chart-line, accent: 4}
""",
    "matrix": """
type: matrix
title: Revenue by quarter
rows:
  - {id: emea, label: EMEA}
  - {id: amer, label: AMER}
  - {id: apac, label: APAC}
columns:
  - {id: q1, label: Q1}
  - {id: q2, label: Q2}
cells:
  - {row: emea, column: q1, label: 1.2M, accent: 0}
  - {row: emea, column: q2, label: 1.4M, accent: 0}
  - {row: amer, column: q1, label: 2.1M, accent: 1}
  - {row: amer, column: q2, label: 2.6M, accent: 1}
  - {row: apac, column: q2, label: 0.8M, accent: 2}
""",
}
