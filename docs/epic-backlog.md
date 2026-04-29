# VisualCeramics Photo Projection Epic Backlog

## Purpose
This backlog is the operational source of truth for the epic:
- user uploads a real room photo;
- the system detects a target surface;
- the user previews VisualCeramics tiles/materials projected onto the photo;
- the flow remains commercially usable even when AI confidence is imperfect.

This document is written so any agent working in any related repository can execute work task by task without needing the entire project history.

## Product Goal
Deliver a realistic and commercially convincing photo-based tile preview flow with:
- low friction for non-technical users;
- strong fallback manual correction;
- incremental rollout;
- stable contracts between AI service, frontend, and the main platform backend.

## Core Principle
Do not optimize for full automation first.
Optimize for a result the user can obtain reliably.

Recommended user experience target:
1. Upload photo.
2. Surface is auto-detected.
3. User sees overlay and confidence.
4. If needed, user adjusts a few points.
5. User selects a real catalog tile.
6. User gets a convincing before/after result.

## Repositories / Workstreams
- `visualceramics-ai`: AI analysis service in Python/FastAPI.
- `visualceramics-front`: image upload, analysis preview, manual correction, tile projection UI.
- main VisualCeramics backend: orchestration, persistence, user/project linkage, security, commercial integration.

## Current State Summary
AI service currently has:
- FastAPI app;
- floor/wall segmentation attempt;
- first-pass geometry output;
- first-pass shadow output;
- modularized backend foundation;
- initial tests scaffold.

Still missing for the epic:
- stable DTO schemas;
- versioned API contract;
- true frontend contract alignment;
- manual correction flow;
- robust homography pipeline;
- catalog-aware projection data;
- persistence/orchestration with the main backend.

## Global Decisions
- The system must always support fallback manual correction.
- Confidence must be explicit in every important analysis result.
- Unknown values must be nullable rather than invented.
- The AI service must not couple itself to one segmentation provider.
- The frontend must be able to continue even when parts of analysis are missing.
- Contracts must be versioned before broad integration.

## Recommended Delivery Order
1. Contract alignment across repos.
2. AI service mock/stable DTO phase.
3. Frontend upload + preview + mock overlay.
4. Frontend manual 4-corner correction.
5. Basic 2D tile projection over the corrected polygon.
6. Catalog integration.
7. Real AI segmentation behind the stable contract.
8. Homography, scale, and lighting improvements.
9. Persistence/export/commercial polish.

## Backlog

### Track A - Cross-Repo Contract And Coordination

#### A-001 Define canonical API version and route
Owner: AI service + frontend + main backend

Task:
- Decide the stable endpoint name for room analysis.
- Recommendation: `POST /api/v1/analyze-room-image`.
- Optional: keep current `POST /api/v1/analyze` as a temporary alias during migration.

Done when:
- route name is documented in the contract;
- frontend knows which route to call;
- alias/deprecation strategy is written down.

Dependencies:
- none

#### A-002 Define `AnalysisRequestDTO`
Owner: AI service

Task:
Define the canonical request payload, including:
- multipart image file;
- optional `target_surface`: `floor | wall | auto`;
- optional manual points;
- optional approximate real dimensions;
- optional selected tile metadata;
- optional `priority_mode`: `speed | balanced | accuracy`.

Done when:
- request fields are documented with types and optionality;
- validation behavior is defined.

Dependencies:
- A-001

#### A-003 Define `AnalysisResultDTO`
Owner: AI service + frontend

Task:
Define a stable JSON response with nullable fields and confidence scores.

Done when:
- DTO is documented;
- frontend consumers know which fields are required vs optional;
- mock and real responses share the same shape.

Dependencies:
- A-001
- A-002

#### A-004 Define frontend compatibility matrix
Owner: frontend + AI service

Task:
Document which fields are used in each frontend phase.

Done when:
- frontend Phase 1, 2, 3 depend only on fields already available or mockable;
- no frontend task depends on undeclared AI output.

Dependencies:
- A-003

#### A-005 Define persistence/orchestration ownership
Owner: main backend + frontend + AI service

Task:
Decide whether:
- frontend uploads directly to AI service;
- frontend uploads to main backend and main backend calls AI service;
- pre-signed storage URLs are involved later.

Recommendation for early phase:
- direct frontend -> AI service for rapid iteration;
- later main backend mediation for auth, persistence, and auditability.

Done when:
- ownership of upload, persistence, and auth is explicit.

Dependencies:
- A-001

### Track B - AI Service Foundation

#### B-001 Add explicit request/response schemas
Owner: AI service

Task:
- Implement Pydantic schemas for request metadata and response DTO.
- Keep response stable even if internals change.

Done when:
- endpoint uses documented schemas;
- mock and real pipeline share the same DTO.

Dependencies:
- A-002
- A-003

#### B-002 Add `MockAnalysisService`
Owner: AI service

Task:
- Provide stable mock analysis independent from SAM/OpenCV.
- Enable frontend integration before real CV is ready.

Done when:
- a mode/config flag exists to return deterministic mock output;
- frontend can develop against it.

Dependencies:
- B-001

#### B-003 Add `ImageValidationService`
Owner: AI service

Task:
Validate:
- MIME type;
- max file size;
- min/max dimensions;
- readable image content.

Done when:
- invalid images fail with structured errors.

Dependencies:
- B-001

#### B-004 Add environment/config management
Owner: AI service

Task:
- define env vars;
- document runtime modes;
- support mock vs real analysis modes.

Done when:
- `.env.example` or equivalent exists;
- README explains local startup.

Dependencies:
- B-001

#### B-005 Add test suite for DTOs and endpoint behavior
Owner: AI service

Task:
Add tests for:
- happy path;
- validation errors;
- mock mode;
- missing optional fields.

Done when:
- tests can run in dependency-ready environments;
- critical contract behavior is covered.

Dependencies:
- B-001
- B-002
- B-003

### Track C - Frontend Integration MVP

#### C-001 Implement image upload flow
Owner: frontend

Task:
- image picker/dropzone;
- client validation;
- multipart upload;
- loading/error/success states.

Done when:
- user can submit a photo and receive an analysis payload.

Dependencies:
- A-001
- A-002
- A-003

#### C-002 Implement analysis preview overlay
Owner: frontend

Task:
Display:
- original image;
- detected mask or polygon;
- target surface label;
- confidence;
- warnings.

Done when:
- user understands what the system detected.

Dependencies:
- C-001

#### C-003 Implement manual corner correction
Owner: frontend

Task:
- draggable corners;
- reset;
- confirm;
- preserve corrected polygon in state.

Done when:
- user can recover from bad AI detection without leaving the flow.

Dependencies:
- C-002

#### C-004 Implement basic 2D projection
Owner: frontend

Task:
- apply tile texture over the selected polygon;
- support repeat/rotation/scale;
- before/after comparison.

Done when:
- user sees a believable projected tile preview.

Dependencies:
- C-003

### Track D - Main Platform Backend Integration

#### D-001 Define orchestration contract with AI service
Owner: main backend

Task:
If the main backend will mediate calls:
- define request proxying strategy;
- define auth propagation;
- define timeout/retry behavior;
- define project storage model.

Done when:
- orchestration boundary is explicit.

Dependencies:
- A-005

#### D-002 Define project persistence model
Owner: main backend

Task:
Store:
- original photo reference;
- analysis result;
- corrected polygon;
- selected tile;
- visualization settings;
- exported result metadata.

Done when:
- project save/reload is possible later.

Dependencies:
- D-001

### Track E - Real AI/CV Pipeline

#### E-001 Introduce segmentation provider interface
Owner: AI service

Task:
- define `SegmentationService` abstraction;
- keep SAM implementation swappable.

Done when:
- mock and real segmentation implement the same interface.

Dependencies:
- B-002

#### E-002 Add real floor/wall segmentation
Owner: AI service

Task:
- integrate SAM 2 or SAM 3 behind the interface;
- return mask + confidence + warnings.

Done when:
- real segmentation works without changing the DTO.

Dependencies:
- E-001

#### E-003 Add surface polygon extraction
Owner: AI service

Task:
- convert masks into usable polygons/corners;
- expose confidence and fallback warnings.

Done when:
- frontend can render editable corners from real analysis.

Dependencies:
- E-002

#### E-004 Add homography estimation
Owner: AI service

Task:
- estimate recommended corners;
- optionally return homography matrix;
- degrade gracefully if confidence is low.

Done when:
- frontend can choose between suggested homography and manual correction.

Dependencies:
- E-003

#### E-005 Add scale estimation
Owner: AI service

Task:
- derive approximate scale from EXIF, manual dimensions, or user calibration.

Done when:
- frontend can repeat tiles based on approximate real dimensions.

Dependencies:
- E-004

#### E-006 Add lighting and shadow hints
Owner: AI service

Task:
- output lighting/shadow hints useful for compositing;
- preserve current shadow artifact evolution path.

Done when:
- frontend can improve visual integration using backend hints.

Dependencies:
- E-003

### Track F - Commercialization Features

#### F-001 Catalog-backed tile selection
Owner: frontend + main backend

Task:
- load real catalog materials;
- pass required texture metadata to the projection UI.

Done when:
- user can preview real VisualCeramics products.

Dependencies:
- C-004
- D-001

#### F-002 Save/reopen project
Owner: main backend + frontend

Done when:
- user can return to a previous room visualization.

Dependencies:
- D-002

#### F-003 Export and compare
Owner: frontend + main backend

Task:
- before/after slider;
- export image;
- shareable preview.

Done when:
- the feature is demo- and sales-ready.

Dependencies:
- F-001

## Execution Notes For Agents
- Do not widen the DTO casually.
- Add new fields as nullable/optional first.
- Never block the user on perfect AI.
- If a task touches frontend and AI service, update the contract doc in the same effort.
- Prefer shipping a mocked but stable end-to-end slice over isolated CV sophistication.

## Definition Of Done For Any Task
A task is only complete when:
- code is implemented in the relevant repo;
- tests or validation are updated where practical;
- docs/contract changes are captured if behavior changed;
- the next dependent team or agent has enough information to continue.
