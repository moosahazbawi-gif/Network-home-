# Panther AI Core

A standalone AI control and execution core for Panther-X2.

## Architecture

- **Core API** — controlled interface between AI and the host system.
- **Tool Runtime** — explicit tools for inspection and execution.
- **Permissions** — execution boundaries and authorization.
- **State / Memory** — persistent operational context.
- **AI Adapter** — model-independent interface for local or remote models.
- **UI boundary** — presentation is intentionally separate from Network Home.

## Principle

AI decides and orchestrates; Panther validates and executes. Every privileged operation must pass through the controlled tool layer.

This directory is intentionally independent from Network Home's application UI.
