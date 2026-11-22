# Face QR Studio

Un face photo + payment QR upload pannunga. Face, QR modules-aale form aagum (halftone block style). Real ZXing validation-oda "Scan Verified" status varum.

## Requirements
- Python 3.12, Node.js LTS

## Backend run
```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\download_models.py
python -m uvicorn app.main:app --reload --port 8000
```

## Frontend run
```powershell
cd frontend
npm install
npm run dev
```
Open http://localhost:3000

## Privacy
- Photos + QR memory-la mattum process aagum, disk-la save aagaadhu.
- Result download aana udane (illa 10 min-la) delete aagum.
- External AI service use pannala.

## Scan note
"Scan Verified" = ZXing 6 checks (100/75/50/35% size, blur, global binarizer) exact payload match. Ella phone-layum 100% guarantee illa. Payment pannum munnaadi unga phone-la scan test pannunga.