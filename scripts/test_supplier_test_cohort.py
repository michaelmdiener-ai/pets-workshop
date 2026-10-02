#!/usr/bin/env python3
"""Tests for the supplier-test-cohort state model.

The harness mirrors the frontend contract without requiring a browser or Shopify
credentials. It verifies the invariants that the React implementation must keep:
separate batches, batch-scoped approvals, persisted renames, and production safety.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


@dataclass
class Product:
    id: str
    name: str


@dataclass
class Batch:
    id: str
    label: str
    created_at: str
    products: List[Product]


class CohortStore:
    """Small persistence-backed model representing the skill's frontend contract."""

    def __init__(self, root: Path):
        self.root = root
        self.history_path = root / "history.json"
        self.production_path = root / "production.json"
        self.approval_prefix = "approvals-"
        self.history: List[Batch] = []
        self.active_batch_id: str | None = None
        self.production_products = [Product("prod-1", "Production product")]
        self._load()

    def _approval_path(self, batch_id: str) -> Path:
        return self.root / f"{self.approval_prefix}{batch_id}.json"

    def _load(self) -> None:
        if self.history_path.exists():
            payload = json.loads(self.history_path.read_text())
            self.history = [
                Batch(
                    item["id"],
                    item["label"],
                    item["created_at"],
                    [Product(**product) for product in item["products"]],
                )
                for item in payload
            ]
        if self.history:
            self.active_batch_id = self.history[0].id

    def _persist_history(self) -> None:
        self.history_path.write_text(json.dumps([asdict(batch) for batch in self.history], indent=2))

    def import_batch(self, batch_id: str, label: str, products: List[Product]) -> Batch:
        batch = Batch(batch_id, label, datetime.now(timezone.utc).isoformat(), list(products))
        self.history = [batch] + [item for item in self.history if item.id != batch_id]
        self.active_batch_id = batch_id
        self._approval_path(batch_id).unlink(missing_ok=True)
        self._persist_history()
        return batch

    def switch_batch(self, batch_id: str) -> Batch:
        batch = next(item for item in self.history if item.id == batch_id)
        self.active_batch_id = batch.id
        return batch

    def active_products(self) -> List[Product]:
        if self.active_batch_id is None:
            return self.production_products
        return self.switch_batch(self.active_batch_id).products

    def approve(self, product_id: str) -> None:
        approvals = self.approvals()
        if product_id not in approvals:
            approvals.append(product_id)
        self._approval_path(self.active_batch_id).write_text(json.dumps(approvals))  # type: ignore[arg-type]

    def approvals(self) -> List[str]:
        if self.active_batch_id is None:
            return []
        path = self._approval_path(self.active_batch_id)
        return json.loads(path.read_text()) if path.exists() else []

    def rename(self, batch_id: str, label: str) -> None:
        normalized = label.strip()
        if not normalized:
            raise ValueError("Batch label cannot be blank")
        self.history = [
            Batch(item.id, normalized if item.id == batch_id else item.label, item.created_at, item.products)
            for item in self.history
        ]
        self._persist_history()


def products(*ids: str) -> List[Product]:
    return [Product(product_id, f"Product {product_id}") for product_id in ids]


class BatchIsolationUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = CohortStore(Path(self.tmp.name))
        self.store.import_batch("batch-a", "Supplier A", products("a-1", "a-2"))
        self.store.import_batch("batch-b", "Supplier B", products("b-1", "b-2"))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_approvals_are_scoped_to_active_batch(self) -> None:
        self.store.switch_batch("batch-a")
        self.store.approve("a-1")
        self.assertEqual(self.store.approvals(), ["a-1"])

        self.store.switch_batch("batch-b")
        self.assertEqual(self.store.approvals(), [])
        self.store.approve("b-1")
        self.assertEqual(self.store.approvals(), ["b-1"])

        self.store.switch_batch("batch-a")
        self.assertEqual(self.store.approvals(), ["a-1"])

    def test_blank_rename_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.store.rename("batch-a", "   ")
        self.assertEqual(self.store.history[-1].label, "Supplier A")


class CohortIntegrationTests(unittest.TestCase):
    def test_import_switch_rename_and_reload_preserve_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = CohortStore(root)
            production_before = list(store.production_products)

            store.import_batch("batch-a", "Initial supplier review", products("a-1"))
            store.approve("a-1")
            store.import_batch("batch-b", "Fresh Shopify drafts", products("b-1", "b-2"))
            self.assertEqual([item.id for item in store.active_products()], ["b-1", "b-2"])
            self.assertEqual(store.approvals(), [])

            store.rename("batch-b", "September supplier review")
            store.switch_batch("batch-a")
            self.assertEqual(store.approvals(), ["a-1"])
            self.assertEqual(store.history[0].label, "September supplier review")
            self.assertEqual(store.production_products, production_before)

            reloaded = CohortStore(root)
            self.assertEqual(reloaded.history[0].label, "September supplier review")
            reloaded.switch_batch("batch-b")
            self.assertEqual(reloaded.approvals(), [])
            self.assertEqual([item.id for item in reloaded.active_products()], ["b-1", "b-2"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
