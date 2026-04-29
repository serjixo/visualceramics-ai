import unittest
from importlib.util import find_spec

HAS_PROCESSING_TEST_DEPS = all(
    find_spec(module_name) is not None
    for module_name in ("cv2", "numpy", "PIL")
)


@unittest.skipUnless(HAS_PROCESSING_TEST_DEPS, "processing dependencies are not installed")
class ProcessingTests(unittest.TestCase):
    def test_resize_for_ai_scales_longest_side_to_target_resolution(self) -> None:
        from PIL import Image

        from visualceramics_ai.processing import resize_for_ai

        image = Image.new("RGB", (2000, 1000), color="white")

        resized = resize_for_ai(image, ai_resolution=1024)

        self.assertEqual(resized.size, (1024, 512))

    def test_get_perspective_metadata_returns_normalized_points(self) -> None:
        import numpy as np

        from visualceramics_ai.processing import get_perspective_metadata

        mask = np.zeros((20, 20), dtype=np.float32)
        mask[5:15, 4:16] = 1.0

        points = get_perspective_metadata(mask)

        self.assertIsNotNone(points)
        assert points is not None
        self.assertGreaterEqual(len(points), 4)
        for x_coord, y_coord in points:
            self.assertGreaterEqual(x_coord, 0.0)
            self.assertLessEqual(x_coord, 1.0)
            self.assertGreaterEqual(y_coord, 0.0)
            self.assertLessEqual(y_coord, 1.0)

    def test_get_perspective_metadata_returns_none_for_empty_mask(self) -> None:
        import numpy as np

        from visualceramics_ai.processing import get_perspective_metadata

        mask = np.zeros((10, 10), dtype=np.float32)

        points = get_perspective_metadata(mask)

        self.assertIsNone(points)


if __name__ == "__main__":
    unittest.main()
