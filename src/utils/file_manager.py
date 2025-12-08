"""
File management utilities for RSS Feed Processor
"""
import os
import shutil
from datetime import datetime
from pathlib import Path
from .logging_config import get_logger

logger = get_logger(__name__)


class SafeFileManager:
    """
    Manages file operations with safe deletion and dated folder creation.
    """

    def __init__(self, base_output_dir, base_temp_dir):
        """
        Initialize the file manager.

        Args:
            base_output_dir: Base directory for output files
            base_temp_dir: Base directory for temporary/deleted files
        """
        self.base_output_dir = Path(base_output_dir)
        self.base_temp_dir = Path(base_temp_dir)

        # Create base directories
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        self.base_temp_dir.mkdir(parents=True, exist_ok=True)

    def create_dated_folder(self, date=None):
        """
        Create a dated folder for today's output.

        Args:
            date: datetime object (default: today)

        Returns:
            Path to the dated folder
        """
        if date is None:
            date = datetime.now()

        folder_name = date.strftime('%Y-%m-%d')
        dated_folder = self.base_output_dir / folder_name
        dated_folder.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created dated folder: {dated_folder}")
        return dated_folder

    def create_temp_folder(self):
        """
        Create a timestamped temporary folder for safe deletion.

        Returns:
            Path to the temp folder
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_folder = self.base_temp_dir / timestamp
        temp_folder.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created temp folder: {temp_folder}")
        return temp_folder

    def safe_delete(self, file_path):
        """
        Safely delete a file by moving it to temp folder instead of permanent deletion.

        Args:
            file_path: Path to file to delete

        Returns:
            Path where file was moved, or None if file doesn't exist
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.warning(f"File doesn't exist, skipping deletion: {file_path}")
            return None

        temp_folder = self.create_temp_folder()
        destination = temp_folder / file_path.name

        # Handle duplicate names
        counter = 1
        while destination.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            destination = temp_folder / f"{stem}_{counter}{suffix}"
            counter += 1

        shutil.move(str(file_path), str(destination))
        logger.info(f"Safely moved file from {file_path} to {destination}")

        return destination

    def safe_delete_folder(self, folder_path):
        """
        Safely delete a folder by moving it to temp folder.

        Args:
            folder_path: Path to folder to delete

        Returns:
            Path where folder was moved, or None if folder doesn't exist
        """
        folder_path = Path(folder_path)

        if not folder_path.exists():
            logger.warning(f"Folder doesn't exist, skipping deletion: {folder_path}")
            return None

        temp_folder = self.create_temp_folder()
        destination = temp_folder / folder_path.name

        # Handle duplicate names
        counter = 1
        while destination.exists():
            destination = temp_folder / f"{folder_path.name}_{counter}"
            counter += 1

        shutil.move(str(folder_path), str(destination))
        logger.info(f"Safely moved folder from {folder_path} to {destination}")

        return destination

    def ensure_dir(self, directory):
        """
        Ensure a directory exists.

        Args:
            directory: Path to directory

        Returns:
            Path object
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def get_file_size(self, file_path):
        """
        Get file size in bytes.

        Args:
            file_path: Path to file

        Returns:
            File size in bytes, or None if file doesn't exist
        """
        file_path = Path(file_path)
        if file_path.exists():
            return file_path.stat().st_size
        return None

    def cleanup_old_temp_folders(self, days=7):
        """
        Clean up temp folders older than specified days.

        Args:
            days: Number of days to keep temp folders
        """
        cutoff = datetime.now().timestamp() - (days * 86400)

        for folder in self.base_temp_dir.iterdir():
            if folder.is_dir():
                if folder.stat().st_mtime < cutoff:
                    shutil.rmtree(folder)
                    logger.info(f"Cleaned up old temp folder: {folder}")
