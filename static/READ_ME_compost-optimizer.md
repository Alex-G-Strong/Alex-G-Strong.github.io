# README: Compost Optimizer - Operations Simulator

**Target Audience:** Future AI Assistant / Developer
**Project Status:** Functional single-page web application (HTML/JS/CSS).

## 1. Core Objective
A front-end JavaScript application designed to optimize compost recipes. It balances chemical requirements (C:N Ratio, Moisture, Bulk Density, Structural Index) against physical constraints (Target Volume, Operator Measurement Units) and hard inventory limits.

## 2. System Architecture & Tech Stack
* **Framework:** Pure Vanilla HTML5, CSS3, and ES6 JavaScript. No external libraries or backend servers required to ensure offline capability in field environments.
* **State Management & Storage:** Internal memory for session calculations; `localStorage` via JSON serialization for long-term retention of custom user ingredients.
* **Unit Agnosticism:** Backend math strictly operates in standard units (Cubic Yards, Pounds). A UI conversion layer handles localized measurements (Loader Buckets, Wheelbarrows, 5-Gallon Buckets).

## 3. Key Logic Decisions & Rationale

### A. The "Strict-to-Relaxed" Priority System
**Decision:** Allow the user to rank Moisture, Bulk Density, and C:N Ratio in order of importance via drag-and-drop.
**Rationale:** In field composting, perfect chemistry is often impossible given available