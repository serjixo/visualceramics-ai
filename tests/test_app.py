import tempfile
import unittest
from importlib.util import find_spec
from pathlib import Path
from unittest.mock import patch

HAS_APP_TEST_DEPS = all(
    find_spec(module_name) is not None
    for module_name in ("fastapi", "torch")
)


@unittest.skipUnless(HAS_APP_TEST_DEPS, "fastapi/torch dependencies are not installed")
class AppFactoryTests(unittest.TestCase):
    def setUp(self) -> None:
        import torch

        from visualceramics_ai.config import AppConfig
        from visualceramics_ai.model_runtime import ModelRuntime

        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.static_dir = self.base_dir / "static"
        self.output_dir = self.static_dir / "masks"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.config = AppConfig(
            base_dir=self.base_dir,
            static_dir=self.static_dir,
            output_dir=self.output_dir,
        )
        self.runtime = ModelRuntime(
            device=torch.device("cpu"),
            model=object(),
            processor=object(),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_static_mask_route_serves_existing_file(self) -> None:
        from fastapi.testclient import TestClient

        from visualceramics_ai.app_factory import create_app

        target_file = self.output_dir / "example.txt"
        target_file.write_text("mask-data")

        client = TestClient(create_app(config=self.config, runtime=self.runtime))
        response = client.get("/static/masks/example.txt")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "mask-data")
        self.assertEqual(response.headers["access-control-allow-origin"], "*")
        self.assertEqual(response.headers["cross-origin-resource-policy"], "cross-origin")

    def test_analyze_route_returns_pipeline_payload(self) -> None:
        from fastapi.testclient import TestClient

        from visualceramics_ai.app_factory import create_app

        app = create_app(config=self.config, runtime=self.runtime)
        expected_payload = {
            "jobId": "abcd1234",
            "masks": {"floor": "/static/masks/abcd1234_floor.png"},
            "shadows": "/static/masks/abcd1234_shadows.png",
            "geometry": {"floor_points": [[0.0, 0.0], [1.0, 1.0]]},
            "width": 100,
            "height": 80,
        }

        with patch("visualceramics_ai.app_factory.analyze_image", return_value=expected_payload) as analyze_mock:
            client = TestClient(app)
            response = client.post(
                "/api/v1/analyze",
                files={"file": ("room.png", b"fake-image-bytes", "image/png")},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_payload)
        analyze_mock.assert_called_once()

    def test_analyze_route_wraps_pipeline_errors(self) -> None:
        from fastapi.testclient import TestClient

        from visualceramics_ai.app_factory import create_app

        app = create_app(config=self.config, runtime=self.runtime)

        with patch("visualceramics_ai.app_factory.analyze_image", side_effect=RuntimeError("boom")):
            client = TestClient(app)
            response = client.post(
                "/api/v1/analyze",
                files={"file": ("room.png", b"fake-image-bytes", "image/png")},
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "boom"})


if __name__ == "__main__":
    unittest.main()
