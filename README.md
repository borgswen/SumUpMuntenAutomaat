# SumUpMuntenAutomaat

Dit project heeft als doel een consumptie-muntenautomaat te bouwen op basis van de SumUp Solo. Via een scherm aan een Raspberry Pi wordt het aantal munten gekozen, SumUp regelt de betaling en na een succesvolle betaling stuurt de Raspberry Pi een muntendispenser aan.

## Backend

De backend bevindt zich in de `backend/` map en is gebouwd met FastAPI, een state machine en driver-abstrahering. Zie `backend/README.md` voor installatie, configuratie en testinstructies.

## Frontend

De frontend bevindt zich in de `frontend/` map en is gebouwd met Vite en React.
