"""Tests for FreezingReviewer GUI application.

This module tests the GUI components using mocking to avoid displaying actual windows.
Tests cover button handling, image navigation, data updates, and file saving.
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

# Try importing tkinter - if not available, skip all tests in this module
pytest.importorskip("tkinter", reason="tkinter not available in this environment")

from olaf.image_verification.freezing_reviewer import FreezingReviewer


@pytest.fixture
def mock_tk_root():
    """Create a mock tkinter root window."""
    mock_root = MagicMock()
    mock_root.title = MagicMock()
    mock_root.quit = MagicMock()
    mock_root.winfo_children = MagicMock(return_value=[])
    return mock_root


@pytest.fixture
def mock_data():
    """Create mock experimental data."""
    data = pd.DataFrame(
        {
            "Picture": ["image1.png", "image2.png", "image3.png"],
            "Avg_Temp": [-5.0, -10.0, -15.0],
            "Sample_0": [0, 5, 10],
            "Sample_1": [0, 3, 8],
            "Sample_2": [0, 2, 6],
            "Sample_3": [0, 1, 4],
            "Sample_4": [0, 1, 3],
            "Sample_5": [0, 0, 2],
            "changes": [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
        }
    )
    return data


@pytest.fixture
def mock_photos(tmp_path):
    """Create mock photo files."""
    images_folder = tmp_path / "test_folder" / "Test_Images"
    images_folder.mkdir(parents=True)

    photos = []
    for i in range(1, 4):
        photo = images_folder / f"image{i}.png"
        photo.write_text("fake image data")
        photos.append(photo)

    return photos


@pytest.fixture
def sample_dilution_dict():
    """Standard dilution dictionary for tests."""
    return {
        "Sample_0": float("inf"),
        "Sample_1": 14641,
        "Sample_2": 1331,
        "Sample_3": 121,
        "Sample_4": 11,
        "Sample_5": 1,
    }


class TestFreezingReviewerInitialization:
    """Test suite for FreezingReviewer initialization."""

    @patch("olaf.image_verification.data_loader.DataHandler.__init__")
    @patch("olaf.image_verification.button_handler.ButtonHandler.create_buttons")
    @patch("olaf.image_verification.button_handler.ButtonHandler.show_photo")
    @patch("olaf.image_verification.data_loader.DataLoader.load_photos")
    def test_initialization_stores_parameters(
        self,
        mock_load_photos,
        mock_show_photo,
        mock_create_buttons,
        mock_data_handler_init,
        mock_tk_root,
        tmp_path,
        sample_dilution_dict,
    ):
        """Test that FreezingReviewer stores all initialization parameters."""
        mock_data_handler_init.return_value = None
        mock_load_photos.return_value = []

        reviewer = FreezingReviewer(
            root=mock_tk_root,
            folder_path=tmp_path,
            num_samples=6,
            wells_per_sample=32,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        assert reviewer.dict_samples_to_dilution == sample_dilution_dict
        assert reviewer.wells_per_sample == 32
        assert reviewer.num_samples == 6


class TestImageNavigation:
    """Test suite for image navigation functionality."""

    @patch("olaf.image_verification.data_loader.DataHandler.__init__")
    @patch("olaf.image_verification.button_handler.ButtonHandler.create_buttons")
    @patch("olaf.image_verification.button_handler.ButtonHandler.show_photo")
    @patch("olaf.image_verification.data_loader.DataLoader.load_photos")
    def test_next_image_increments_index(
        self,
        mock_load_photos,
        mock_show_photo,
        mock_create_buttons,
        mock_data_handler_init,
        mock_tk_root,
        tmp_path,
        sample_dilution_dict,
        mock_photos,
    ):
        """Test that _next_image increments the photo index."""
        mock_data_handler_init.return_value = None
        mock_load_photos.return_value = mock_photos

        reviewer = FreezingReviewer(
            root=mock_tk_root,
            folder_path=tmp_path,
            num_samples=6,
            wells_per_sample=32,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        # Reset the mock to clear initialization call
        mock_show_photo.reset_mock()

        reviewer.current_photo_index = 0
        reviewer._next_image()

        assert reviewer.current_photo_index == 1
        assert mock_show_photo.called

    @patch("olaf.image_verification.data_loader.DataHandler.__init__")
    @patch("olaf.image_verification.button_handler.ButtonHandler.create_buttons")
    @patch("olaf.image_verification.button_handler.ButtonHandler.show_photo")
    @patch("olaf.image_verification.data_loader.DataLoader.load_photos")
    @patch("olaf.image_verification.button_handler.ButtonHandler.closing_sequence")
    def test_next_image_at_end_closes_gui(
        self,
        mock_closing_sequence,
        mock_load_photos,
        mock_show_photo,
        mock_create_buttons,
        mock_data_handler_init,
        mock_tk_root,
        tmp_path,
        sample_dilution_dict,
        mock_photos,
    ):
        """Test that _next_image closes GUI when at end of photos."""
        mock_data_handler_init.return_value = None
        mock_load_photos.return_value = mock_photos
        mock_closing_sequence.return_value = None

        reviewer = FreezingReviewer(
            root=mock_tk_root,
            folder_path=tmp_path,
            num_samples=6,
            wells_per_sample=32,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        reviewer.current_photo_index = len(mock_photos) - 1
        reviewer._next_image()

        assert reviewer.current_photo_index == len(mock_photos)
        assert mock_closing_sequence.called
        assert mock_tk_root.quit.called

    @patch("olaf.image_verification.data_loader.DataHandler.__init__")
    @patch("olaf.image_verification.button_handler.ButtonHandler.create_buttons")
    @patch("olaf.image_verification.button_handler.ButtonHandler.show_photo")
    @patch("olaf.image_verification.data_loader.DataLoader.load_photos")
    def test_prev_image_decrements_index(
        self,
        mock_load_photos,
        mock_show_photo,
        mock_create_buttons,
        mock_data_handler_init,
        mock_tk_root,
        tmp_path,
        sample_dilution_dict,
        mock_photos,
    ):
        """Test that _prev_image decrements the photo index."""
        mock_data_handler_init.return_value = None
        mock_load_photos.return_value = mock_photos

        reviewer = FreezingReviewer(
            root=mock_tk_root,
            folder_path=tmp_path,
            num_samples=6,
            wells_per_sample=32,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        reviewer.current_photo_index = 2
        reviewer._prev_image()

        assert reviewer.current_photo_index == 1

    @patch("olaf.image_verification.data_loader.DataHandler.__init__")
    @patch("olaf.image_verification.button_handler.ButtonHandler.create_buttons")
    @patch("olaf.image_verification.button_handler.ButtonHandler.show_photo")
    @patch("olaf.image_verification.data_loader.DataLoader.load_photos")
    def test_prev_image_at_start_does_nothing(
        self,
        mock_load_photos,
        mock_show_photo,
        mock_create_buttons,
        mock_data_handler_init,
        mock_tk_root,
        tmp_path,
        sample_dilution_dict,
        mock_photos,
    ):
        """Test that _prev_image does nothing when at start."""
        mock_data_handler_init.return_value = None
        mock_load_photos.return_value = mock_photos

        reviewer = FreezingReviewer(
            root=mock_tk_root,
            folder_path=tmp_path,
            num_samples=6,
            wells_per_sample=32,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        reviewer.current_photo_index = 0
        reviewer._prev_image()

        assert reviewer.current_photo_index == 0


class TestDataUpdates:
    """Test suite for data update functionality."""

    @patch("olaf.image_verification.data_loader.DataHandler.__init__")
    @patch("olaf.image_verification.button_handler.ButtonHandler.create_buttons")
    @patch("olaf.image_verification.button_handler.ButtonHandler.show_photo")
    @patch("olaf.image_verification.data_loader.DataLoader.load_photos")
    def test_update_image_increases_frozen_count(
        self,
        mock_load_photos,
        mock_show_photo,
        mock_create_buttons,
        mock_data_handler_init,
        mock_tk_root,
        tmp_path,
        sample_dilution_dict,
        mock_photos,
        mock_data,
    ):
        """Test that _update_image correctly increases frozen well count."""
        mock_data_handler_init.return_value = None
        mock_load_photos.return_value = mock_photos

        reviewer = FreezingReviewer(
            root=mock_tk_root,
            folder_path=tmp_path,
            num_samples=6,
            wells_per_sample=32,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        # Set up test data
        reviewer.data = mock_data.copy()
        reviewer.photos = mock_photos
        reviewer.current_photo_index = 1

        # Mock the display methods
        reviewer._display_num_frozen = MagicMock()
        reviewer._display_current_temp = MagicMock()

        original_value = reviewer.data.loc[1, "Sample_0"]
        reviewer._update_image(sample=0, change=1)

        # Value should increase by 1 for current and all subsequent rows
        assert reviewer.data.loc[1, "Sample_0"] == original_value + 1
        assert reviewer.data.loc[2, "Sample_0"] == original_value + 1

    @patch("olaf.image_verification.data_loader.DataHandler.__init__")
    @patch("olaf.image_verification.button_handler.ButtonHandler.create_buttons")
    @patch("olaf.image_verification.button_handler.ButtonHandler.show_photo")
    @patch("olaf.image_verification.data_loader.DataLoader.load_photos")
    def test_update_image_respects_max_wells(
        self,
        mock_load_photos,
        mock_show_photo,
        mock_create_buttons,
        mock_data_handler_init,
        mock_tk_root,
        tmp_path,
        sample_dilution_dict,
        mock_photos,
        mock_data,
    ):
        """Test that _update_image enforces maximum wells_per_sample limit."""
        mock_data_handler_init.return_value = None
        mock_load_photos.return_value = mock_photos

        reviewer = FreezingReviewer(
            root=mock_tk_root,
            folder_path=tmp_path,
            num_samples=6,
            wells_per_sample=32,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        reviewer.data = mock_data.copy()
        reviewer.photos = mock_photos
        reviewer.current_photo_index = 2

        # Mock the display methods
        reviewer._display_num_frozen = MagicMock()
        reviewer._display_current_temp = MagicMock()

        # Set value near max and try to exceed
        reviewer.data.loc[2, "Sample_0"] = 32
        reviewer._update_image(sample=0, change=5)

        # Should be capped at wells_per_sample
        assert reviewer.data.loc[2, "Sample_0"] == 32

    @patch("olaf.image_verification.data_loader.DataHandler.__init__")
    @patch("olaf.image_verification.button_handler.ButtonHandler.create_buttons")
    @patch("olaf.image_verification.button_handler.ButtonHandler.show_photo")
    @patch("olaf.image_verification.data_loader.DataLoader.load_photos")
    def test_update_image_prevents_negative_values(
        self,
        mock_load_photos,
        mock_show_photo,
        mock_create_buttons,
        mock_data_handler_init,
        mock_tk_root,
        tmp_path,
        sample_dilution_dict,
        mock_photos,
        mock_data,
    ):
        """Test that _update_image prevents negative frozen well counts."""
        mock_data_handler_init.return_value = None
        mock_load_photos.return_value = mock_photos

        reviewer = FreezingReviewer(
            root=mock_tk_root,
            folder_path=tmp_path,
            num_samples=6,
            wells_per_sample=32,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        reviewer.data = mock_data.copy()
        reviewer.photos = mock_photos
        reviewer.current_photo_index = 0

        # Mock the display methods
        reviewer._display_num_frozen = MagicMock()
        reviewer._display_current_temp = MagicMock()

        reviewer.data.loc[0, "Sample_0"] = 0
        reviewer._update_image(sample=0, change=-1)

        # Should remain at 0
        assert reviewer.data.loc[0, "Sample_0"] == 0


class TestDisplayMethods:
    """Test suite for display functionality."""

    @patch("olaf.image_verification.data_loader.DataHandler.__init__")
    @patch("olaf.image_verification.button_handler.ButtonHandler.create_buttons")
    @patch("olaf.image_verification.button_handler.ButtonHandler.show_photo")
    @patch("olaf.image_verification.data_loader.DataLoader.load_photos")
    def test_display_current_temp_creates_label_on_first_call(
        self,
        mock_load_photos,
        mock_show_photo,
        mock_create_buttons,
        mock_data_handler_init,
        mock_tk_root,
        tmp_path,
        sample_dilution_dict,
        mock_photos,
        mock_data,
    ):
        """Test that _display_current_temp creates temperature label on first call."""
        mock_data_handler_init.return_value = None
        mock_load_photos.return_value = mock_photos

        reviewer = FreezingReviewer(
            root=mock_tk_root,
            folder_path=tmp_path,
            num_samples=6,
            wells_per_sample=32,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        reviewer.data = mock_data.copy()

        # Initially temp_label should be None
        assert reviewer.temp_label is None

        # Call display_current_temp
        with patch("tkinter.LabelFrame") as mock_label_frame, patch(
            "tkinter.Label"
        ) as mock_label:
            mock_temp_frame = MagicMock()
            mock_temp_label = MagicMock()
            mock_label_frame.return_value = mock_temp_frame
            mock_label.return_value = mock_temp_label

            reviewer._display_current_temp(current_index=1)

            # Should create label frame and label
            assert mock_label_frame.called
            assert mock_label.called

    @patch("olaf.image_verification.data_loader.DataHandler.__init__")
    @patch("olaf.image_verification.button_handler.ButtonHandler.create_buttons")
    @patch("olaf.image_verification.button_handler.ButtonHandler.show_photo")
    @patch("olaf.image_verification.data_loader.DataLoader.load_photos")
    def test_display_num_frozen_shows_all_samples(
        self,
        mock_load_photos,
        mock_show_photo,
        mock_create_buttons,
        mock_data_handler_init,
        mock_tk_root,
        tmp_path,
        sample_dilution_dict,
        mock_photos,
        mock_data,
    ):
        """Test that _display_num_frozen displays all sample values."""
        mock_data_handler_init.return_value = None
        mock_load_photos.return_value = mock_photos

        reviewer = FreezingReviewer(
            root=mock_tk_root,
            folder_path=tmp_path,
            num_samples=6,
            wells_per_sample=32,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        reviewer.data = mock_data.copy()

        with patch("tkinter.LabelFrame"), patch("tkinter.Label"), patch("tkinter.Frame"):
            # Should not raise any errors
            reviewer._display_num_frozen("image2.png")


class TestErrorHandling:
    """Test suite for error handling."""

    @patch("olaf.image_verification.data_loader.DataHandler.__init__")
    @patch("olaf.image_verification.button_handler.ButtonHandler.create_buttons")
    @patch("olaf.image_verification.button_handler.ButtonHandler.show_photo")
    @patch("olaf.image_verification.data_loader.DataLoader.load_photos")
    def test_update_image_raises_error_for_missing_picture(
        self,
        mock_load_photos,
        mock_show_photo,
        mock_create_buttons,
        mock_data_handler_init,
        mock_tk_root,
        tmp_path,
        sample_dilution_dict,
        mock_photos,
        mock_data,
    ):
        """Test that _update_image raises error when picture not found in data."""
        mock_data_handler_init.return_value = None
        mock_load_photos.return_value = mock_photos

        reviewer = FreezingReviewer(
            root=mock_tk_root,
            folder_path=tmp_path,
            num_samples=6,
            wells_per_sample=32,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        reviewer.data = mock_data.copy()
        reviewer.photos = [Path("nonexistent.png")]
        reviewer.current_photo_index = 0

        with pytest.raises(ValueError, match="No data found for picture"):
            reviewer._update_image(sample=0, change=1)


class TestAdvancedNavigation:
    """Test suite for advanced navigation (±10 images)."""

    @patch("olaf.image_verification.data_loader.DataHandler.__init__")
    @patch("olaf.image_verification.button_handler.ButtonHandler.create_buttons")
    @patch("olaf.image_verification.button_handler.ButtonHandler.show_photo")
    @patch("olaf.image_verification.data_loader.DataLoader.load_photos")
    def test_advance_10_images(
        self,
        mock_load_photos,
        mock_show_photo,
        mock_create_buttons,
        mock_data_handler_init,
        mock_tk_root,
        tmp_path,
        sample_dilution_dict,
    ):
        """Test that _advance_10_images moves forward by 10."""
        mock_data_handler_init.return_value = None

        # Create more photos for this test
        many_photos = [Path(f"image{i}.png") for i in range(20)]
        mock_load_photos.return_value = many_photos

        reviewer = FreezingReviewer(
            root=mock_tk_root,
            folder_path=tmp_path,
            num_samples=6,
            wells_per_sample=32,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        reviewer.current_photo_index = 0
        reviewer._advance_10_images()

        assert reviewer.current_photo_index == 10

    @patch("olaf.image_verification.data_loader.DataHandler.__init__")
    @patch("olaf.image_verification.button_handler.ButtonHandler.create_buttons")
    @patch("olaf.image_verification.button_handler.ButtonHandler.show_photo")
    @patch("olaf.image_verification.data_loader.DataLoader.load_photos")
    def test_reverse_10_images(
        self,
        mock_load_photos,
        mock_show_photo,
        mock_create_buttons,
        mock_data_handler_init,
        mock_tk_root,
        tmp_path,
        sample_dilution_dict,
    ):
        """Test that _reverse_10_images moves back by 10."""
        mock_data_handler_init.return_value = None

        many_photos = [Path(f"image{i}.png") for i in range(20)]
        mock_load_photos.return_value = many_photos

        reviewer = FreezingReviewer(
            root=mock_tk_root,
            folder_path=tmp_path,
            num_samples=6,
            wells_per_sample=32,
            dict_samples_to_dilution=sample_dilution_dict,
            includes=("test1",),
        )

        reviewer.current_photo_index = 15
        reviewer._reverse_10_images()

        assert reviewer.current_photo_index == 5
