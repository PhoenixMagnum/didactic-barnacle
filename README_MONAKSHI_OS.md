# House of Monakshi OS

A founder-operated command centre for House of Monakshi.

This is not a second storefront and not a replacement for Wix, the payment gateway, Instagram or Metricool. It is the operating layer behind them.

## What v1 does

- Launch command centre with explicit gates and blockers
- Supplier scoring built around Monakshi's actual operating model
- Product unit economics and hard launch-readiness gates
- Local document vault for supplier catalogues, terms and research
- Supplier/competitor URL watchlist with change detection
- Brand-safe caption and product-copy generator
- Safe demo data for a public repository

## Privacy rule

This repository is public. Never commit supplier negotiated rates tied to identifiable suppliers, supplier emails or phone numbers, customer data, payment data, private catalogues, contracts, API tokens or OAuth credentials.

Real operating data belongs in the local SQLite database at data/monakshi.db or an authenticated private system. The data directory is gitignored.

## Run

Python 3.10+ recommended.

1. Create a virtual environment.
2. Install requirements.txt.
3. Run: streamlit run app.py

## Product launch gate

A product is not launch-ready until its sample, burn test, packaging test, product photography and specifications are approved and its contribution margin clears the configured floor.

## Architecture

Wix remains the storefront. The payment gateway remains the payment rail. Metricool and Instagram remain publishing surfaces. Monakshi OS owns supplier intelligence, product qualification, document evidence, monitoring, launch readiness and brand operating rules.

## Next adapters

Later adapters can connect Gmail, Google Drive, Wix exports, Metricool/Meta and payment reconciliation without rewriting the core domain logic.
