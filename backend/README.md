# Backend

Deze backend is ontworpen als een architectuurgerichte kioskservice met:
- `FastAPI` voor HTTP en WebSocket communicatie
- een centrale `StateMachine` voor statusbeheer
- `PaymentService`, `HopperService` en `TransactionService`
- configuratie via `config.yaml` en secrets via een lokale `secret.yaml`
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
  - `sumup_api_base`
  - `sumup_merchant_code`
  - `sumup_affiliate_app_id`
  - `sumup_affiliate_key`
  - `sumup_reader_id`
  - `sumup_reader_code`
  - `sumup_currency`
  - `payment_timeout_seconds`
  - `simulation.enabled`
  - `simulation.payment.mode`
  - `simulation.payment.delay_ms`
  - `simulation.hopper.speed`
  - `simulation.hopper.capacity`
  - `simulation.hopper.start_amount`
  - `simulation.hopper.jam_probability`
  - `simulation.hopper.random_failures`

- `backend/secrets.example.yaml` bevat alleen het voorbeeldveld `sumup_api_key`.
- Kopieer `backend/secrets.example.yaml` naar `backend/secret.yaml` voor lokale secret waarden. `backend/secret.yaml` wordt niet gedeeld.
- Zet echte SumUp secrets nooit in `config.yaml` of in Git.

## SumUp Solo Cloud API

Simulator mode blijft standaard actief. De echte SumUp Solo-driver wordt pas gebruikt wanneer `use_simulator: false` en `simulation.enabled: false` staan.

### API key maken

1. Open het SumUp Dashboard.
2. Ga naar `For Developers` en daarna `API Keys`.
3. Maak een nieuwe secret API key aan met de benodigde rechten voor Readers/Transactions.
4. Kopieer de key direct, want SumUp toont hem maar een keer.
5. Zet de key lokaal in `backend/secret.yaml`:

```yaml
sumup_api_key: "<your_sumup_api_key>"
```

### Solo koppelen

Voor de Solo Cloud API heb je een gekoppelde reader nodig. Laat de Solo een pairing code tonen en maak daarna via de SumUp API een reader aan:

```powershell
$env:SUMUP_API_KEY = "<your_sumup_api_key>"
$merchantCode = "<sumup_merchant_code>"
$headers = @{
  Authorization = "Bearer $env:SUMUP_API_KEY"
  "Content-Type" = "application/json"
}
$body = @{
  pairing_code = "<pairing_code_van_de_solo>"
  name = "SumUpMuntenAutomaat Solo"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "https://api.sumup.com/v0.1/merchants/$merchantCode/readers" `
  -Headers $headers `
  -Body $body
```

Neem de teruggegeven `id` over in `backend/config.yaml` als `sumup_reader_id`.

Je kunt tijdelijk ook `sumup_reader_code` invullen. Dan probeert de backend bij startup te koppelen en logt hij de ontvangen reader id. Voor normaal gebruik is `sumup_reader_id` stabieler.

### Wisselen naar SumUp mode

Vul in `backend/config.yaml` minimaal deze velden:

```yaml
use_simulator: false
sumup_api_base: https://api.sumup.com
sumup_merchant_code: "<merchant_code>"
sumup_affiliate_app_id: sumup-muntenautomaat
sumup_affiliate_key: "<affiliate_key>"
sumup_reader_id: "<reader_id>"
sumup_reader_code: ""
sumup_currency: EUR
payment_timeout_seconds: 30
simulation:
  enabled: false
```

Let op: in de huidige architectuur schakelt `use_simulator: false` ook de echte hopper-driver in. Gebruik deze stand alleen op de machine-installatie met hardware. Voor development zonder hardware blijft simulator mode de juiste keuze.

Referenties:
- SumUp Solo Cloud API overview: https://developer.sumup.com/terminal-payments/cloud-api/
- Reader checkout endpoint: https://developer.sumup.com/api/readers/create-checkout
- API key setup: https://developer.sumup.com/tools/authorization/api-keys/

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
