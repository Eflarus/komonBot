from src.utils.image_validation import sanitize_filename


class TestSanitizeFilename:
    def test_generates_uuid_based_name(self):
        name = sanitize_filename("photo.jpg", "image/jpeg")
        assert name.endswith(".jpg")
        assert len(name) == 36  # 32 hex chars + 4 for ".jpg"

    def test_ignores_original_filename(self):
        name = sanitize_filename("../../etc/passwd", "image/png")
        assert "/" not in name
        assert ".." not in name
        assert name.endswith(".png")

    def test_correct_extension_for_webp(self):
        name = sanitize_filename("image.jpg", "image/webp")
        assert name.endswith(".webp")

    def test_handles_none_filename(self):
        name = sanitize_filename(None, "image/jpeg")
        assert name.endswith(".jpg")
        assert len(name) > 4

    def test_unique_names(self):
        names = {sanitize_filename("a.jpg", "image/jpeg") for _ in range(100)}
        assert len(names) == 100

    def test_no_path_separators(self):
        name = sanitize_filename("path/to/../../file.png", "image/png")
        assert "\\" not in name
        assert "/" not in name
