"""
Data Migration Module
====================

Provides a migration system for handling data schema changes across versions.
"""

import json
import logging
from pathlib import Path
from typing import Any

from app.persistence import PersistenceManager


class DataMigrator:
    """
    Manages data migrations for the application.

    Migrations are executed sequentially and tracked in storage/state.json.
    Each migration is a closure that operates on raw data dictionaries.
    """

    def __init__(self, persistence_manager: PersistenceManager) -> None:
        """
        Initialize the data migrator.

        Args:
            persistence_manager: The persistence manager for loading/saving raw data
        """
        self.persistence_manager = persistence_manager
        self.state_file = Path("storage/state.json")
        self._logger = logging.getLogger(__name__)

        # List of migrations - each is a function that will be called in order
        self.migrations = [
            self._migration_0_add_field_order,
            # Future migrations go here
        ]

    def run(self) -> None:
        """
        Run all pending migrations.

        Loads the last executed migration index from state.json,
        then runs all migrations that haven't been executed yet.
        """
        last_migration = self._load_migration_state()

        # Run all migrations after the last executed one
        for idx in range(last_migration + 1, len(self.migrations)):
            self._logger.info(f"Running migration {idx}...")
            try:
                self.migrations[idx]()
                self._save_migration_state(idx)
                self._logger.info(f"Migration {idx} completed successfully")
            except Exception as e:
                self._logger.error(
                    f"Migration {idx} failed: {type(e).__name__} - {e}",
                    exc_info=True,
                )
                raise

    def _migration_0_add_field_order(self) -> None:
        """
        Migration 0: Add order property to all fields.

        For each list, iterate through its fields and add an "order" property
        based on the iteration order (0, 1, 2, ...).
        """
        self._logger.info("Migration 0: Adding order property to all fields")

        # Load all lists as raw dicts
        lists = self.persistence_manager.load_all_raw()

        if not lists:
            self._logger.info("No lists to migrate")
            return

        migrated_count = 0
        for list_id, list_data in lists.items():
            fields = list_data.get("fields", {})

            if not fields:
                continue

            # Check if migration is needed (any field missing order or all orders are 0)
            needs_migration = False
            field_orders = []

            for field_data in fields.values():
                order = field_data.get("order", None)
                if order is None:
                    needs_migration = True
                    break
                field_orders.append(order)

            # Also check if all orders are 0 (default value)
            if not needs_migration and len(set(field_orders)) == 1 and field_orders[0] == 0:
                needs_migration = len(field_orders) > 1  # Only if there are multiple fields

            if needs_migration:
                # Assign sequential orders based on iteration order
                for idx, field_data in enumerate(fields.values()):
                    field_data["order"] = idx

                # Save the modified list back to disk
                self.persistence_manager.write_raw_to_disk(list_id, list_data)
                migrated_count += 1
                self._logger.debug(f"Migrated field orders for list {list_id}")

        self._logger.info(f"Migrated {migrated_count} lists")

    def _load_migration_state(self) -> int:
        """
        Load the last executed migration index from state.json.

        Returns:
            The index of the last executed migration, or -1 if no migrations have run
        """
        if not self.state_file.exists():
            self._logger.info("No migration state found, starting from beginning")
            return -1

        try:
            content = self.state_file.read_text(encoding="utf-8")
            state = json.loads(content)
            last_migration = state.get("last_migration", -1)
            self._logger.info(f"Last executed migration: {last_migration}")
            return last_migration
        except Exception as e:
            self._logger.warning(
                f"Failed to load migration state: {type(e).__name__} - {e}. Starting from beginning."
            )
            return -1

    def _save_migration_state(self, migration_index: int) -> None:
        """
        Save the current migration index to state.json.

        Args:
            migration_index: The index of the migration that was just executed
        """
        try:
            # Ensure storage directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            state = {"last_migration": migration_index}
            content = json.dumps(state, indent=2)
            self.state_file.write_text(content, encoding="utf-8")

            self._logger.debug(f"Saved migration state: {migration_index}")
        except Exception as e:
            self._logger.error(
                f"Failed to save migration state: {type(e).__name__} - {e}",
                exc_info=True,
            )
            raise
