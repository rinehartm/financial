# Financial transaction integration (all linked bank accounts)

This project gives you a ready-to-run integration for pulling transaction data from all your connected bank accounts using **Plaid**.

## What "all bank accounts" means in practice

No public API can directly pull data from every bank with just your username/password in a safe way.
The standard approach is to use an aggregator (like Plaid), connect each institution through a consent flow, then pull transactions from each connected **Item**.

This integration handles that pull step.

## Features

- Create a Plaid Link token for bank-connection UI.
- Exchange `public_token` for long-lived `access_token`.
- Pull transactions incrementally using `/transactions/sync` with pagination.
- Emit a JSON payload with `added`, `modified`, `removed`, and `next_cursor`.

## Setup

1. Create a Plaid account and get credentials.
2. Set environment variables:

```bash
export PLAID_CLIENT_ID="your_client_id"
export PLAID_SECRET="your_secret"
export PLAID_ENV="sandbox"   # or development / production
```

3. Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### 1) Pull transactions for one linked item

```bash
python bank_transactions_integration.py --access-token "access-sandbox-..."
```

### 2) Incremental sync (recommended)

Store the returned `next_cursor` and pass it next run:

```bash
python bank_transactions_integration.py \
  --access-token "access-sandbox-..." \
  --cursor "previous_cursor"
```

## Integrating into your app

You can import `PlaidTransactionsClient` and call:

- `create_link_token(user_id)`
- `exchange_public_token(public_token)`
- `sync_transactions(access_token, cursor=None)`

In production, store each user's tokens and cursors securely (encrypted at rest), and never expose secrets client-side.

## Notes

- You must run your own frontend for Plaid Link to collect `public_token`.
- To pull from *all* your accounts, users must connect each institution they use.
- If you prefer a different aggregator (MX, Finicity, Teller), I can adapt this integration.
