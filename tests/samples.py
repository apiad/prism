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
}
