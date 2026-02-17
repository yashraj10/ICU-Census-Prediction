# Data

This directory should contain the source Excel files. They are **not committed to Git**
because they contain de-identified hospital data and are too large for version control.

## Required files

| File | Description | Approximate size |
|------|-------------|-----------------|
| `Daily inpatient level of care.xlsx` | Per-encounter LOS by unit (ICU, Med/Surg, PCU, Tele) | ~2 MB |
| `Teletracking02.24_01.25DEID.xlsx` | De-identified TeleTracking bed request timestamps, care level, ED throughput times | ~5 MB |

## Key columns

### Daily Inpatient Level of Care
- `Proxy_Enc_ID` — De-identified encounter identifier
- `ICU`, `Med_Surg`, `PCU`, `Tele` — Days spent in each unit
- `Total` — Total length of stay

### TeleTracking
- `Bedrequest Timestamp` — When a bed was requested
- `Requested Level Of Care` — ICU, Med/Surg, PCU, Tele, etc.
- `ED Bed Request To Bed Occupy Time` — Minutes from ED request to bed occupancy
- `Rtm To Bedassigned Time` — Minutes from room-ready to bed assignment

## Reproducing

Place both `.xlsx` files in this directory, then run:

```bash
python src/pipeline.py --data-dir data/
```
