# Video Editor Backend (Skeleton)

## Requirements
- Python 3.10+

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

## Run
```bash
uvicorn backend.main:app --reload
```

Open Swagger UI at `http://127.0.0.1:8000/docs`.

## API Flow
1. `POST /auth/register`
2. `POST /auth/login`
3. `GET /me` with `Authorization: Bearer <access_token>`
4. `POST /worksheet/generate` with `Authorization: Bearer <access_token>`

## Optional: OpenAI Content Generation
Set `OPENAI_API_KEY` to generate worksheets via OpenAI. Without it, a template generator is used.
