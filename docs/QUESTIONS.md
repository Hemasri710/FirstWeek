## 10 Real Questions My Users Will Ask

| #  | Question                                                                   | Where the answer is (document/file)                                | Needs more than one page? |
| -- | -------------------------------------------------------------------------- | ------------------------------------------------------------------ | ------------------------- |
| 1  | How does FastAPI know which function to call when I use `Depends()`?       | Dependencies documentation, `fastapi/dependencies/utils.py`        | Yes                       |
| 2  | Why am I getting a 422 error when I send incorrect data to my API?         | Request Body documentation, `fastapi/routing.py`                   | Yes                       |
| 3  | What is the difference between `Depends()` and `Security()`?               | Security documentation, `fastapi/params.py`                        | Yes                       |
| 4  | How does FastAPI know which API function to run when I visit a URL?        | Path Operation documentation, `fastapi/routing.py`                 | No                        |
| 5  | If something goes wrong in my API, how does FastAPI handle the error?      | Handling Errors documentation, `fastapi/exception_handlers.py`     | No                        |
| 6  | How does FastAPI automatically create Swagger UI documentation for my API? | Metadata and Docs documentation, `fastapi/openapi/utils.py`        | Yes                       |
| 7  | What happens if I use `async def` in FastAPI, and why is it useful?        | Async documentation, `fastapi/routing.py`                          | Yes                       |
| 8  | How does FastAPI convert the data I return into a JSON response?           | Response Model documentation, `fastapi/routing.py`                 | Yes                       |
| 9  | What happens when one dependency needs another dependency to work?         | Sub-dependencies documentation, `fastapi/dependencies/utils.py`    | Yes                       |
| 10 | What is my company's actual production database password?                  | Cannot be found in the public FastAPI documentation or source code | No                        |