# VisualCeramics Photo Analysis Integration Contract

## Purpose
This document defines the recommended contract between:
- AI analysis service;
- frontend photo projection experience;
- main VisualCeramics backend.

It is intentionally designed to support:
- mock responses first;
- real CV implementation later;
- graceful degradation;
- manual correction when AI confidence is low.

## Recommended Endpoint Strategy
Canonical endpoint:
- `POST /api/v1/analyze-room-image`

Temporary compatibility option:
- keep `POST /api/v1/analyze` as an alias until the frontend is migrated.

Recommendation:
- choose one canonical route now;
- mark any other route as legacy in docs and code comments.

## Transport
Request content type:
- `multipart/form-data`

Fields:
- `file`: required image file
- `targetSurface`: optional string enum `floor | wall | auto`
- `priorityMode`: optional string enum `speed | balanced | accuracy`
- `manualPoints`: optional JSON string or optional separate JSON body in a later version
- `realDimensions`: optional JSON string in the early multipart version
- `selectedTile`: optional JSON string in the early multipart version

Note:
For MVP compatibility, keep the request simple. If multipart metadata becomes awkward, define a two-step flow later.

## Request DTO
Recommended conceptual shape:

```json
{
  "targetSurface": "auto",
  "priorityMode": "balanced",
  "manualPoints": {
    "surface": "floor",
    "points": [[0.1, 0.8], [0.9, 0.8], [0.85, 0.35], [0.2, 0.35]]
  },
  "realDimensions": {
    "widthMeters": 3.5,
    "depthMeters": 4.2
  },
  "selectedTile": {
    "tileId": "tile-123",
    "widthMm": 600,
    "heightMm": 600
  }
}
```

## Response DTO
Recommended stable shape:

```json
{
  "jobId": "abcd1234",
  "status": "ok",
  "surface": {
    "target": "floor",
    "detected": "floor",
    "confidence": 0.91,
    "maskUrl": "/static/masks/abcd1234_floor.png",
    "polygon": {
      "points": [[0.08, 0.86], [0.92, 0.83], [0.82, 0.34], [0.17, 0.36]],
      "confidence": 0.84,
      "source": "ai"
    },
    "recommendedCorners": {
      "points": [[0.08, 0.86], [0.92, 0.83], [0.82, 0.34], [0.17, 0.36]],
      "confidence": 0.79,
      "editable": true
    }
  },
  "projection": {
    "homographyMatrix": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    "confidence": 0.42,
    "vanishingPoints": [],
    "camera": {
      "fovDegrees": null,
      "focalLengthMm": null,
      "lensDistortion": null,
      "confidence": 0.0
    },
    "scale": {
      "pixelsPerMeter": null,
      "source": "unknown",
      "confidence": 0.0
    }
  },
  "lighting": {
    "shadowMapUrl": "/static/masks/abcd1234_shadows.png",
    "direction": null,
    "intensity": null,
    "temperatureKelvin": null,
    "confidence": 0.15
  },
  "image": {
    "width": 1440,
    "height": 1080,
    "exif": {
      "available": false,
      "focalLengthMm": null,
      "cameraModel": null
    }
  },
  "warnings": [
    "Low homography confidence. Manual corner adjustment recommended."
  ],
  "fallbacks": {
    "manualCornerAdjustmentRecommended": true,
    "manualScaleCalibrationRecommended": true
  },
  "debug": {
    "analysisMode": "mock"
  }
}
```

## Rules For Nullable Data
- Never invent camera, scale, lighting, or homography values.
- Return `null` when unavailable.
- Pair uncertain outputs with `confidence`.
- Use `warnings` and `fallbacks` to guide the frontend UX.

## Frontend Minimum Required Fields By Phase

### Phase 1 - Upload / basic response
Required:
- `jobId`
- `status`
- `image.width`
- `image.height`
- `warnings`

### Phase 2 - Analysis preview
Required:
- `surface.detected`
- `surface.confidence`
- `surface.maskUrl` or `surface.polygon`

### Phase 3 - Basic projection
Required:
- `surface.recommendedCorners.points` or `surface.polygon.points`
- `image.width`
- `image.height`

### Phase 4 - Manual correction
Required:
- editable points
- fallback flags

### Phase 5+ - Realism improvements
Useful:
- `projection.homographyMatrix`
- `projection.scale`
- `lighting.shadowMapUrl`
- `lighting.direction`

## Error Contract
Recommended error shape:

```json
{
  "error": {
    "code": "INVALID_IMAGE",
    "message": "The uploaded file is not a valid supported image.",
    "details": {
      "acceptedMimeTypes": ["image/jpeg", "image/png", "image/webp"]
    }
  }
}
```

Recommended error codes:
- `INVALID_IMAGE`
- `UNSUPPORTED_MIME_TYPE`
- `IMAGE_TOO_LARGE`
- `IMAGE_TOO_SMALL`
- `ANALYSIS_UNAVAILABLE`
- `ANALYSIS_TIMEOUT`
- `INTERNAL_ERROR`

## Ownership Recommendations
Early iteration:
- frontend calls AI service directly.

Later production:
- main backend mediates access, authentication, persistence, rate limits, and project linkage.

## Versioning Recommendation
If the contract evolves materially:
- keep `/api/v1/...` stable as long as possible;
- prefer additive changes;
- if a breaking change is necessary, introduce `/api/v2/...`.

## Open Questions To Resolve Against Frontend Repo
- Which route name is already hardcoded today?
- Which exact fields does the current frontend already expect?
- Is the frontend using mask URL, raw points, or both?
- Does the frontend already carry tile size metadata?
- Where should manual correction state be persisted?
