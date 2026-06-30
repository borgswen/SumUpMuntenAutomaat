# SumUpMuntenAutomaat

Dit project heeft als doel een consumptie-muntenautomaat te bouwen op basis van de SumUp Solo. Via een scherm aan een Raspberry Pi wordt het aantal munten gekozen, SumUp regelt de betaling en na een succesvolle betaling stuurt de Raspberry Pi een muntendispenser aan. Dit project is nog ongetest en  vooral ook een oefening om te zien hoeveel je kan programmeren met AI zonder enige serieuze kennis over programmeren. De grote lijnen zijn bedacht met chatgpt, de frontend is gegenereed door figma en de back end geschreven door codex en copilot.

## Backend

De backend bevindt zich in de `backend/` map en is gebouwd met FastAPI, een state machine en driver-abstrahering. Zie `backend/README.md` voor installatie, configuratie en testinstructies.

## Frontend

De frontend bevindt zich in de `frontend/` map en is gebouwd met Vite en React.


Dingen draaien voor test:

Backend
```console
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Check daarna:

http://localhost:8000/docs
Frontend

Open een tweede terminal:
```console
cd frontend
npm install
npm run dev
```
Open daarna de URL die Vite geeft, meestal:

http://localhost:5173
