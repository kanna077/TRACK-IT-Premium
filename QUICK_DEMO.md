# TRACK-IT 10-Minute Demonstration

## Start

Open two PowerShell terminals.

Terminal 1:

```powershell
.\run-backend.ps1
```

Terminal 2:

```powershell
.\run-frontend.ps1
```

Open `http://localhost:3000`.

## Demo accounts

Run once when needed:

```powershell
.\.venv\Scripts\Activate.ps1
python backend\manage.py seed_demo
```

```text
admin1   / TrackIt@2026
student1 / TrackIt@2026
finder1  / TrackIt@2026
```

## Recommended presentation sequence

1. **Premium dashboard** — show metrics, recent reports and responsive layout.
2. **Lost & Found** — show search, filters, status labels and images.
3. **AI Matches** — sign in as `student1`, open the lost wallet and run matching.
4. **Email OTP** — register an External Finder using an inbox you can access.
5. **Private claim** — submit hidden ownership evidence for the found wallet.
6. **Administrator review** — sign in as `admin1` and approve the claim.
7. **Secure QR + OTP** — display the QR, token and OTP.
8. **Handover** — complete the return and show the generated receipt.
9. **Single-use security** — attempt the same token again and show rejection.
10. **Messages and notifications** — demonstrate secure claim messages and updates.
11. **Exports** — download PDF and Excel reports.
12. **Assistant** — ask how ownership claims work.

## Key explanation for reviewers

> TRACK-IT uses AI to rank possible matches, but the score is informational only. Ownership is decided using private evidence, authorized review and a single-use QR + OTP handover.
