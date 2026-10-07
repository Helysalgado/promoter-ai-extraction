---
technical_level: technical
project_kind: software
---

# User profile

Goal: Build promoter-ai-extraction, an AI Engineering system for evidence-grounded extraction of bacterial promoter properties from scientific literature. Given a TEI/XML or TXT article and an identified promoter, the system must extract TSS, -10 box, -35 box, and sigma factor information with traceable evidence, normalization, support for multiple values, and explicit abstention when evidence is insufficient. The system must be objectively evaluated against a curator-reviewed gold set without exposing target values to the extractor. The project should be developed incrementally, starting with a guided extraction baseline and evaluation pipeline, then adding RAG, agents, an MVP interface, and deployment as required by the final course project and justified by observed needs. The existing Markdown files in the repository root are the authoritative scientific, evaluation, gold-set, extraction, and UX requirements and must not be modified without explicit human approval. Development may use feature branches; main represents consolidated work, and the final course submission must be delivered from branch finalproject-HSO.
