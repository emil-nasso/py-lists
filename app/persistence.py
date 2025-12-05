import json
import logging
import shutil
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from app.models import List


class PersistenceManager:
    """
    Manages disk-based persistence for List objects.

    Storage structure:
        storage/lists/{list-id}/list.json
    """

    def __init__(self, storage_root: Path) -> None:
        """
        Initialize the persistence manager.

        Args:
            storage_root: Root directory for storage (relative to project root)
        """
        self._storage_root = storage_root
        self._lists_dir = self._storage_root / "lists"
        self._logger = logging.getLogger(__name__)

    def load_all(self) -> dict[UUID, List]:
        """
        Load all lists from disk.

        Returns:
            Dictionary mapping list IDs to List objects

        Raises:
            OSError: If there are file system access issues
        """
        if not self._lists_dir.exists():
            self._logger.info("Storage directory does not exist. Starting with empty storage.")
            return {}

        lists: dict[UUID, List] = {}
        loaded_count = 0
        skipped_count = 0

        for list_dir in self._lists_dir.iterdir():
            if not list_dir.is_dir():
                continue

            # Validate directory name is a valid UUID
            try:
                list_id = UUID(list_dir.name)
            except ValueError:
                self._logger.warning(f"Skipping directory with invalid UUID name: {list_dir.name}")
                skipped_count += 1
                continue

            # Load list.json file
            list_file = self._get_list_file(list_id)
            if not list_file.exists():
                self._logger.warning(f"Skipping directory {list_dir.name}: list.json not found")
                skipped_count += 1
                continue

            try:
                json_content = list_file.read_text(encoding="utf-8")
                list_obj = List.model_validate_json(json_content)
                lists[list_id] = list_obj
                loaded_count += 1
            except ValidationError as e:
                self._logger.warning(
                    f"Skipping corrupted list {list_id}: Pydantic validation error - {e}"
                )
                skipped_count += 1
            except Exception as e:
                self._logger.warning(
                    f"Skipping list {list_id} due to error: {type(e).__name__} - {e}"
                )
                skipped_count += 1

        if skipped_count > 0:
            self._logger.info(
                f"Loaded {loaded_count} lists from storage (skipped {skipped_count} with errors)"
            )
        else:
            self._logger.info(f"Loaded {loaded_count} lists from storage")

        return lists

    def load_all_raw(self) -> dict[str, dict[str, Any]]:
        """
        Load all lists from disk as raw dictionaries without Pydantic validation.
        Used by the migration system to work with raw data.

        Returns:
            Dictionary mapping list ID strings to raw list data dicts

        Raises:
            OSError: If there are file system access issues
        """
        if not self._lists_dir.exists():
            self._logger.info("Storage directory does not exist. No lists to migrate.")
            return {}

        lists: dict[str, dict[str, Any]] = {}
        loaded_count = 0
        skipped_count = 0

        for list_dir in self._lists_dir.iterdir():
            if not list_dir.is_dir():
                continue

            # Validate directory name is a valid UUID
            try:
                UUID(list_dir.name)
                list_id = list_dir.name
            except ValueError:
                self._logger.warning(f"Skipping directory with invalid UUID name: {list_dir.name}")
                skipped_count += 1
                continue

            # Load list.json file
            list_file = list_dir / "list.json"
            if not list_file.exists():
                self._logger.warning(f"Skipping directory {list_dir.name}: list.json not found")
                skipped_count += 1
                continue

            try:
                json_content = list_file.read_text(encoding="utf-8")
                list_data = json.loads(json_content)
                lists[list_id] = list_data
                loaded_count += 1
            except json.JSONDecodeError as e:
                self._logger.warning(f"Skipping corrupted list {list_id}: JSON decode error - {e}")
                skipped_count += 1
            except Exception as e:
                self._logger.warning(
                    f"Skipping list {list_id} due to error: {type(e).__name__} - {e}"
                )
                skipped_count += 1

        if skipped_count > 0:
            self._logger.info(
                f"Loaded {loaded_count} raw lists from disk (skipped {skipped_count} with errors)"
            )
        else:
            self._logger.info(f"Loaded {loaded_count} raw lists from disk")

        return lists

    def write_raw_to_disk(self, list_id: str, list_data: dict[str, Any]) -> None:
        """
        Write a raw list dictionary to its JSON file without validation.
        Used by the migration system.

        Args:
            list_id: The list ID as a string
            list_data: The raw list data dictionary

        Raises:
            OSError: If there are file system write issues
        """
        list_dir = self._lists_dir / list_id
        list_file = list_dir / "list.json"
        tmp_file = list_file.with_suffix(".json.tmp")

        try:
            # Create directory if needed
            list_dir.mkdir(parents=True, exist_ok=True)

            # Write to temporary file
            json_content = json.dumps(list_data, indent=2)
            tmp_file.write_text(json_content, encoding="utf-8")

            # Atomic rename
            tmp_file.rename(list_file)

            self._logger.debug(f"Persisted raw list {list_id} to disk")

        except Exception as e:
            self._logger.error(
                f"Failed to persist raw list {list_id} to disk: {type(e).__name__} - {e}",
                exc_info=True,
            )
            # Clean up temporary file if it exists
            if tmp_file.exists():
                tmp_file.unlink()
            raise

    def write_to_disk(self, list: List) -> None:
        """
        Write a single list to its JSON file.

        Args:
            list: The List object to persist

        Raises:
            OSError: If there are file system write issues
        """
        list_dir = self._get_list_dir(list.id)
        list_file = self._get_list_file(list.id)
        tmp_file = list_file.with_suffix(".json.tmp")

        try:
            # Create directory if needed
            list_dir.mkdir(parents=True, exist_ok=True)

            # Write to temporary file
            json_content = list.model_dump_json(indent=2)
            tmp_file.write_text(json_content, encoding="utf-8")

            # Atomic rename
            tmp_file.rename(list_file)

            self._logger.debug(f"Persisted list {list.id} to disk")

        except Exception as e:
            self._logger.error(
                f"Failed to persist list {list.id} to disk: {type(e).__name__} - {e}",
                exc_info=True,
            )
            # Clean up temporary file if it exists
            if tmp_file.exists():
                tmp_file.unlink()
            raise

    def delete_from_disk(self, list_id: UUID) -> bool:
        """
        Delete a list's directory and contents from disk.

        Args:
            list_id: The ID of the list to delete

        Returns:
            True if deleted, False if list didn't exist on disk
        """
        list_dir = self._get_list_dir(list_id)

        if not list_dir.exists():
            return False

        try:
            shutil.rmtree(list_dir)
            self._logger.debug(f"Deleted list {list_id} from disk")
            return True
        except Exception as e:
            self._logger.error(
                f"Failed to delete list {list_id} from disk: {type(e).__name__} - {e}",
                exc_info=True,
            )
            raise

    def _get_list_dir(self, list_id: UUID) -> Path:
        """Get the directory path for a specific list."""
        return self._lists_dir / str(list_id)

    def _get_list_file(self, list_id: UUID) -> Path:
        """Get the JSON file path for a specific list."""
        return self._get_list_dir(list_id) / "list.json"
