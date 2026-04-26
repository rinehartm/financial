"""Plaid-based integration for pulling transaction data across linked bank accounts.

This module provides a small client you can run as a script or import into your own app.
It uses Plaid's /transactions/sync endpoint so you can ingest incremental updates.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class PlaidConfig:
    client_id: str
    secret: str
    environment: str = "sandbox"

    @property
    def base_url(self) -> str:
        hosts = {
            "sandbox": "https://sandbox.plaid.com",
            "development": "https://development.plaid.com",
            "production": "https://production.plaid.com",
        }
        try:
            return hosts[self.environment]
        except KeyError as exc:
            valid = ", ".join(sorted(hosts))
            raise ValueError(f"Invalid Plaid environment '{self.environment}'. Expected one of: {valid}") from exc


class PlaidTransactionsClient:
    def __init__(self, config: PlaidConfig, session: requests.Session | None = None) -> None:
        self.config = config
        self.session = session or requests.Session()

    def create_link_token(self, user_id: str) -> dict[str, Any]:
        """Create a Link token you use on your frontend to connect an account."""
        payload = {
            "client_id": self.config.client_id,
            "secret": self.config.secret,
            "client_name": "Financial Transaction Puller",
            "country_codes": ["US"],
            "language": "en",
            "products": ["transactions"],
            "user": {"client_user_id": user_id},
        }
        return self._post("/link/token/create", payload)

    def exchange_public_token(self, public_token: str) -> dict[str, Any]:
        """Exchange a short-lived public token for a long-lived access token."""
        payload = {
            "client_id": self.config.client_id,
            "secret": self.config.secret,
            "public_token": public_token,
        }
        return self._post("/item/public_token/exchange", payload)

    def sync_transactions(
        self,
        access_token: str,
        cursor: str | None = None,
        count: int = 100,
    ) -> dict[str, Any]:
        """Fetch added/modified/removed transactions incrementally.

        Returns a dict with keys:
        - added
        - modified
        - removed
        - next_cursor
        - has_more
        """
        payload = {
            "client_id": self.config.client_id,
            "secret": self.config.secret,
            "access_token": access_token,
            "count": count,
            "options": {},
        }
        if cursor:
            payload["cursor"] = cursor

        added: list[dict[str, Any]] = []
        modified: list[dict[str, Any]] = []
        removed: list[dict[str, Any]] = []

        has_more = True
        next_cursor = cursor

        while has_more:
            if next_cursor:
                payload["cursor"] = next_cursor
            response = self._post("/transactions/sync", payload)
            added.extend(response.get("added", []))
            modified.extend(response.get("modified", []))
            removed.extend(response.get("removed", []))
            has_more = bool(response.get("has_more", False))
            next_cursor = response.get("next_cursor", next_cursor)

        return {
            "added": added,
            "modified": modified,
            "removed": removed,
            "next_cursor": next_cursor,
            "has_more": False,
        }

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.config.base_url}{path}"
        response = self.session.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()


def load_config_from_env() -> PlaidConfig:
    client_id = os.getenv("PLAID_CLIENT_ID")
    secret = os.getenv("PLAID_SECRET")
    environment = os.getenv("PLAID_ENV", "sandbox")

    if not client_id or not secret:
        raise RuntimeError("Missing PLAID_CLIENT_ID and/or PLAID_SECRET environment variables")

    return PlaidConfig(client_id=client_id, secret=secret, environment=environment)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pull transactions from all linked bank accounts via Plaid")
    parser.add_argument("--access-token", required=True, help="Plaid access token for one linked Item")
    parser.add_argument("--cursor", default=None, help="Previous sync cursor for incremental updates")
    parser.add_argument(
        "--output",
        default=f"transactions_{dt.datetime.now(tz=dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json",
        help="Output JSON file path",
    )

    args = parser.parse_args()

    config = load_config_from_env()
    client = PlaidTransactionsClient(config)
    result = client.sync_transactions(access_token=args.access_token, cursor=args.cursor)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Wrote {len(result['added'])} added, {len(result['modified'])} modified, {len(result['removed'])} removed")
    print(f"Next cursor: {result['next_cursor']}")
    print(f"Saved file: {args.output}")


if __name__ == "__main__":
    main()
