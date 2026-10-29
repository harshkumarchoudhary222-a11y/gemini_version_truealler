# gemini_version_truealler

Clean-room Telegram phone-metadata bot based on the observable behavior of the reference bot screenshots. It does not copy private source code, credentials, private databases, or bypass provider protections.

## Review of the previous approach

The original design was a useful UI prototype, but it had important correctness problems:

- Server 2 copied Server 1's name, so it was not actually an independent source.
- The Telegram link was malformed.
- "Last Seen: 0 seconds ago" was fabricated.
- Premium was only a message; no payment state existed.
- The ad callback claimed an ad was viewed without an actual sponsored-link flow.
- Credits were deducted before validation and the daily-credit logic would not refill correctly.
- Provider failures were silently indistinguishable from a genuine "not found".
- User/provider text was not consistently escaped for HTML.
- The database/cache design was not used consistently.

## Improved architecture

Telegram -> aiogram -> validation/normalization -> independent providers -> result formatter.

Server 1 — Directory provider: optional adapter for a legitimate caller-name/directory API configured by you.

Server 2 — Phone metadata: Google's open-source libphonenumber dataset for validation, country, number type, timezone, geographic description and original carrier metadata where available.

This deliberately does not claim that libphonenumber can provide the current subscriber name. A Truecaller-like caller identity database requires a separate provider with appropriate data rights.

## Setup

1. Create a Telegram bot with @BotFather.
2. Copy .env.example to .env.
3. Add BOT_TOKEN.
4. Optionally configure a legitimate directory API with DIRECTORY_API_URL and DIRECTORY_API_KEY.
5. Install: pip install -r requirements.txt
6. Run: python bot.py

## Tests

Run pytest -q.

GitHub Actions runs the same test suite on pushes and pull requests.

## Next development phase

The next useful step is provider benchmarking: test several legitimate APIs against the same authorized test numbers and compare name/carrier/location coverage, latency, limits, price and terms. Then implement only the providers that actually improve coverage.
