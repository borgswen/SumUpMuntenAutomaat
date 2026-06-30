# SumUpMuntenAutomaat
Dit project heeft als doel een consumptie muntenautomaat te bouwen op basis van de SumUp solo. Via een scherm aan een raspberry pi wordt het aantal munten gekozen, sumup regelt de betaling, als die succesvol is stuurt de raspberry pi een munten dispenser aan voor het juiste aantal munten.

## Backend
De backend bevindt zich in de `backend/` map en is gebouwd met FastAPI, een state machine en driver-abstrahering. Zie `backend/README.md` voor installatie, configuratie en testinstructies.

> De oude `app/` map is legacy en wordt niet gebruikt. Het actieve backendpakket is `backend/app/`.
