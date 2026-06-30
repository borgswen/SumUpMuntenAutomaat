# Backend

Deze backend is ontworpen als een architectuurgerichte kioskservice met:
- `FastAPI` voor HTTP en WebSocket communicatie
- een centrale `StateMachine` voor statusbeheer
- `PaymentService`, `HopperService` en `TransactionService`
- configuratie via `config.yaml` en secrets via `secret.yaml`
- simulator drivers voor development zonder hardware of SumUp

## Installatie

1. Maak een Python-virtuele omgeving aan:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Installeer dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```

## Configuratie

- `backend/config.yaml` bevat app config:
  - `price_per_coin`
  - `preset_amounts`
  - `use_simulator`
  - `database_path`
  - `simulator.payment_behavior`
  - `simulator.payment_timeout_seconds`
  - `simulator.hopper_behavior`

- `backend/secret.yaml` bevat SumUp credentials wanneer `use_simulator: false`.

## Runnen

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Tests

```powershell
pytest
```

## Architectuur

- `app/core` bevat configuratie, events en state machine.
- `app/drivers` bevat hardware/simulator-abstrahering.
- `app/services` bevat domeinlogica voor betaling, hopper en transacties.
- `app/api` bevat API- en WebSocket-laag.
- `app/database` bevat SQLite-persistentie.
