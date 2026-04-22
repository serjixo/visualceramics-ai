# AGENTS.md

## Product Goal
This repository exists to power a ceramic tile visualization feature.

The end goal is to let users upload photos of their own spaces and preview catalog tiles applied to those spaces in a convincing, production-ready way.

The realism target is not limited to placing a texture on the floor. The system must progressively support:
- floor and wall recognition;
- projection of tile materials with correct perspective deformation;
- preservation or reconstruction of shadows and contact darkening;
- handling of occlusions from furniture, walls, objects, and architectural edges;
- geometry and metadata that a Three.js client can use to render believable results.

This means the backend should evolve from a simple mask generator into a scene-analysis service that provides the data needed for high-quality compositing and projection.

## Current Repository State
The repository currently contains a small FastAPI service centered on `server.py`.

Today it already attempts to:
- load the `facebook/sam3` model through `transformers`;
- accept an uploaded image at `POST /api/v1/analyze`;
- generate floor and wall masks;
- derive basic geometry from masks;
- generate a first-pass shadow/light map for the floor;
- write generated artifacts under `static/masks/`.

## Repository Layout
- `server.py`: main API, model loading, segmentation, geometry extraction, and shadow processing.
- `static/`: static asset directory.
- `static/masks/`: generated runtime outputs.
- `prueba.jpeg`: sample image asset.

## Runtime Expectations
Use Python for this project.

The current code imports these libraries:
- `fastapi`
- `uvicorn`
- `python-multipart`
- `Pillow`
- `opencv-python`
- `numpy`
- `torch`
- `transformers`

The model initialization currently chooses the device in this order:
1. `mps`
2. `cuda`
3. `cpu`

Expect first startup to be heavy because the model may need to be downloaded and loaded into memory.

## Run Commands
Start the API locally with one of these commands:

```bash
python3 server.py
```

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

Default local URL:
- `http://localhost:8000`

Current endpoint:
- `POST /api/v1/analyze`

## Engineering Standards
This project must follow strong engineering discipline even though the current implementation is small.

When working in this repository:
- apply SOLID principles where they fit naturally;
- refactor toward clear separation of responsibilities instead of growing a monolithic script;
- avoid technical debt whenever possible;
- if a shortcut is temporarily necessary, document it clearly and contain its impact;
- keep code readable, testable, and easy to reason about;
- prefer explicit data contracts over implicit behavior;
- avoid magic constants unless they are named and justified;
- favor deterministic outputs and stable response shapes;
- preserve backwards compatibility of API contracts unless a contract change is explicitly requested;
- do not use project size as a reason to lower clean-code standards.

## Refactor Direction
The long-term direction is to split the current script into responsibilities such as:
- API layer;
- configuration and settings;
- model loading and inference;
- segmentation post-processing;
- geometry and perspective extraction;
- shadow and lighting extraction;
- serialization of API responses and artifacts.

Refactors should aim to improve maintainability without changing behavior unless behavior changes are part of the task.

## Product Expectations
The backend should incrementally evolve to support a realistic tile-visualization pipeline.

Capabilities that already exist in some form:
- floor detection;
- wall detection;
- basic polygon extraction;
- first-pass shadow extraction.

Capabilities that are expected to be added incrementally:
- more reliable floor-plane estimation;
- perspective or homography metadata for projection;
- confidence scoring;
- occlusion masks for furniture and objects;
- improved shadow transfer and relighting support;
- scale or calibration support for tile sizing;
- structured output that the Three.js frontend can consume directly;
- fallback and correction mechanisms for cases where AI is uncertain.

## Incremental Delivery Strategy
Work should proceed in phases.

### Phase 1: Stabilize The Existing Analyzer
Focus on:
- dependency management;
- API hardening;
- code organization;
- deterministic outputs;
- basic validation and tests.

### Phase 2: Improve Scene Understanding
Focus on:
- better mask quality;
- better geometry extraction;
- confidence metrics;
- structured analysis artifacts.

### Phase 3: Projection Metadata
Focus on:
- floor-plane reconstruction;
- perspective or homography data;
- calibration hooks;
- support for manual correction where needed.

### Phase 4: Realism And Compositing
Focus on:
- shadow preservation;
- occlusion preservation;
- lighting-aware blending;
- more convincing integration with the original photo.

### Phase 5: Production Readiness
Focus on:
- observability;
- error handling;
- cleanup of generated artifacts;
- performance;
- deployment readiness.

## Testing Expectations
Testing is required as this project grows.

Minimum expectations:
- syntax or import validation for every meaningful backend change;
- unit tests for pure processing utilities when code is extracted into functions or modules;
- regression tests for mask, geometry, and response-shape behavior where practical;
- smoke tests for the analyze endpoint;
- sample-image based checks for high-risk visual-processing changes.

If a change is difficult to test automatically, the limitation should be stated explicitly and the code should still be structured to make future tests easier.

## Agent Guidelines
When working in this repository:
- treat the current API behavior as the baseline until a new contract is agreed;
- prefer incremental improvements over large speculative rewrites;
- keep the backend aligned with the future Three.js integration needs;
- surface better approaches when the current path is technically weak;
- call out missing pieces, assumptions, and risks instead of hiding them;
- optimize for realism, maintainability, and extensibility together.

## Validation
For small changes, validate with:

```bash
python3 -m py_compile server.py
```

If runtime dependencies are installed, also validate by starting the server and exercising `POST /api/v1/analyze` with a sample image.
