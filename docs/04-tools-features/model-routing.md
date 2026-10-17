---
id: model-routing
sidebar_position: 20
title: AI model routing (planned)
---

# AI model routing (planned)

BotStacks is developing an optional model-routing integration. **This page describes a proposed feature under review, not a feature available in the current product.** No customer action is required.

Model routing matches an assistant's workload to an approved AI model and compatible hosting provider. BotStacks will continue to supply the assistant's knowledge and instructions. Different model choices can affect answer quality, response time and operating cost.

## Proposed choices

| Choice | Intended use |
| --- | --- |
| Cost-smart | Routine questions grounded in the assistant's knowledge |
| Faster replies | Interactive conversations where response time matters |
| More accurate | More demanding generation tasks after quality evaluation |
| Explicit model | An approved model selected by an advanced operator |

An explicit model selection is intended to stay pinned to that model. Automatic policies may use approved alternatives when a model or provider is unavailable. Availability depends on the configured privacy, capability and price requirements.

## What remains the same

Existing assistants will keep their current model behavior until explicitly migrated. Knowledge retrieval and citations remain part of BotStacks. Model routing does not change or re-index existing knowledge embeddings.

## Limits and cost

Routing does not guarantee cheaper or more accurate responses. A single provider account can already offer several models; the benefit of a routing layer comes from measured workload matching and compatible provider alternatives. Actual costs depend on token usage, model choice and provider fees.

BotStacks will evaluate quality, grounding, latency, schema/tool compatibility and cost before enabling this integration. Production budgets, access controls and release approval are required. Feature availability and pricing will be announced after validation.
