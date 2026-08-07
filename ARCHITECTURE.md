# ARCHITECTURE.md

# GTA Radio Simulator Architecture

Version: 1.0

---

# Project Goal

Create a cross-platform GTA Radio Simulator that reproduces the behavior of the original GTA radio stations while remaining:

* deterministic;
* maintainable;
* easy to debug;
* lightweight;
* fast even on HDD;
* identical on Windows, Linux and macOS.

The project is **not** a clone of GTRadio.

Only the radio logic is inspired by the original project.

The implementation, architecture and user interface are completely independent.

---

# Design Philosophy

The project follows several simple principles.

1. Keep the code simple.
2. Hide implementation details.
3. Avoid unnecessary abstractions.
4. Avoid premature optimization.
5. Prefer deterministic behavior.
6. Every module has a single responsibility.

---

# Public API

The project exposes only one public object.

```text
RadioEngine
```

Everything else is considered an internal implementation detail.

GUI, CLI and tests should communicate only with `RadioEngine`.

---

# High-Level Architecture

```text
GUI / CLI
        │
        ▼
+----------------+
|  RadioEngine   |
+----------------+
        │
        ├───────────────┐
        ▼               ▼
LibraryManager     AudioPlayer
        │               │
        ▼               ▼
 GenXLoader       miniaudio
        │
        ▼
 StationLibrary
```

---

# Project Structure

```text
radio/

├── engine.py
├── errors.py
├── constants.py
│
├── audio/
│   ├── player.py
│   ├── decoder.py
│   ├── device.py
│   └── metadata.py
│
├── library/
│   ├── manager.py
│   ├── loader.py
│   ├── gen1.py
│   ├── gen2.py
│   └── gen3.py
│
├── model/
│
└── util/
```

---

# Responsibilities

## RadioEngine

Responsibilities:

* load radio library;
* switch stations;
* control playback;
* expose public API.

Must not:

* parse directories;
* decode audio;
* read metadata.

---

## LibraryManager

Responsibilities:

* choose correct loader;
* build StationLibrary;
* hide loader implementations.

---

## Gen1 / Gen2 / Gen3 Loader

Responsibilities:

* validate directory structure;
* create model objects;
* never play audio.

---

## AudioPlayer

Responsibilities:

* audio playback;
* interaction with miniaudio.

Must not:

* know anything about GTA generations.

---

## MetadataReader

Responsibilities:

* read audio metadata;
* calculate duration.

Must not:

* expose mutagen to the rest of the project.

---

## Filesystem

Responsibilities:

* directory scanning;
* file filtering;
* path normalization.

Must not:

* know anything about stations.

---

# Data Model

Immutable models:

* Song
* Station
* StationLibrary

Mutable model:

* StationState

Models contain data only.

Business logic belongs elsewhere.

---

# Time

The entire project uses milliseconds.

```text
Milliseconds
```

No floating-point time values are used internally.

Current time is obtained only from:

```python
time.monotonic_ns()
```

---

# Errors

Only project-specific exceptions may leave internal modules.

```text
RadioError
│
├── LibraryError
└── AudioError
```

Third-party exceptions must be converted before crossing subsystem boundaries.

---

# Filesystem Rules

Only `pathlib.Path` is used.

No:

* os.path
* glob.glob()

Directory order is deterministic using case-insensitive sorting.

---

# Audio Rules

Only one module knows each external dependency.

```text
audio/player.py
    ↓
miniaudio
```

```text
audio/metadata.py
    ↓
mutagen
```

Every other module remains independent.

---

# Performance Goals

The simulator must:

* start quickly;
* switch stations with minimal delay;
* work correctly on HDD;
* avoid unnecessary disk access;
* avoid unnecessary allocations.

Optimization is introduced only after measurement.

---

# Threading

The preferred execution model is synchronous.

Threads are avoided unless there is a measurable benefit.

Asynchronous programming is avoided unless absolutely necessary.

This greatly simplifies debugging and eliminates most race conditions.

---

# Determinism

Given the same library and the same starting conditions:

* station order is identical;
* playback logic is identical;
* timing behavior is identical.

Platform differences must not affect simulation logic.

---

# Coding Rules

* one class = one responsibility;
* one function = one responsibility;
* strong typing everywhere;
* minimal public API;
* implementation details remain private.

---

# Git Workflow

One commit = one completed task.

Every commit must:

* compile;
* pass a quick manual test;
* keep the project functional.

---

# Long-Term Goal

The architecture should support:

* Gen1 stations
* Gen2 stations
* Gen3 stations

without changing the public API.

New features should be added by extending internal modules rather than modifying external interfaces.

---

# Final Principle

The project values readability and correctness over cleverness.

Simple code that is easy to understand is preferred over complex code that is only marginally faster.

The architecture should allow future contributors to understand the project quickly and modify it safely without introducing regressions.
