from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import AppConfig, load_config
from .model_runtime import ModelRuntime, load_model_runtime
from .pipeline import analyze_image


def create_app(config: AppConfig | None = None, runtime: ModelRuntime | None = None) -> FastAPI:
    app_config = config or load_config()
    app_runtime = runtime or load_model_runtime()
    app = FastAPI(title="VisualCeramics AI - Ultra Shadow Catcher")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    @app.get("/static/masks/{file_path:path}")
    async def get_static_resource(file_path: str):
        file_full_path = app_config.output_dir / file_path
        if not file_full_path.is_file():
            raise HTTPException(status_code=404)

        return FileResponse(
            str(file_full_path),
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cross-Origin-Resource-Policy": "cross-origin",
                "Cache-Control": "no-cache",
            },
        )

    app.mount("/static", StaticFiles(directory=str(app_config.static_dir)), name="static")

    @app.post("/api/v1/analyze")
    def analyze_scene(file: UploadFile = File(...)):
        try:
            return analyze_image(file.file.read(), runtime=app_runtime, config=app_config)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        finally:
            file.file.close()

    return app
