# FirstWeek

## Problem

New developers often struggle to understand how FastAPI works internally when they join a software company. They may hesitate to ask senior developers basic questions, and general AI chatbots can sometimes provide incorrect technical answers. FirstWeek helps developers understand FastAPI by answering questions using its actual source code and documentation. It provides code references and responds with "I don't know" when sufficient evidence is unavailable.

## Who it is for

- Fresher backend developers joining software companies that use FastAPI.
- Junior Python developers who want to understand FastAPI's internal implementation.

## Signature feature

An AI assistant that answers FastAPI questions using actual source-code evidence and refuses to guess when the available code does not support an answer.

## Hardest problem (my interview story)

The hardest problem is preventing the AI from generating incorrect answers about FastAPI internals. FirstWeek must retrieve the correct source code, provide evidence for its answers, and respond "I don't know" when the available information is insufficient. I will evaluate its faithfulness and hallucination rate using a 100-question test set.

## Dataset

| Source | Link | Documents | Pages | Licence / terms |
|---|---|---|---|---|
| FastAPI source code and documentation | https://github.com/fastapi/fastapi | To be counted after indexing | To be counted after indexing | MIT License; verify the licence for individual files and dependencies |

## 10 real questions

See [docs/QUESTIONS.md](docs/QUESTIONS.md).

## Run it

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements-dev.txt

# Windows
copy .env.example .env

uvicorn app.main:app --reload
```

Check the health endpoint:

```bash
curl http://localhost:8000/health
```

## Live link

in Week 2.
