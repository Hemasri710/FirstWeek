import os
import threading

import psycopg

DB = os.getenv("DATABASE_URL")
_mem, _lock = [], threading.Lock()


def init():
    if not DB:
        return
    try:
        with psycopg.connect(DB, connect_timeout=3) as c:
            c.execute("CREATE EXTENSION IF NOT EXISTS vector")
            c.execute(
                """CREATE TABLE IF NOT EXISTS usage_log(
                  id SERIAL PRIMARY KEY, ts TIMESTAMPTZ DEFAULT now(), model TEXT,
                  input_tokens INT, output_tokens INT,
                  cost_usd DOUBLE PRECISION, latency_ms INT)"""
            )
    except Exception as e:
        print("db init failed:", e)


def log(model, tin, tout, cost, ms):
    row = (model, tin, tout, cost, ms)
    with _lock:
        _mem.append(row)
    if DB:
        try:
            with psycopg.connect(DB, connect_timeout=3) as c:
                c.execute(
                    "INSERT INTO usage_log"
                    "(model,input_tokens,output_tokens,cost_usd,latency_ms) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    row,
                )
        except Exception as e:
            print("usage log failed:", e)


def summary():
    agg = {}
    for m, i, o, c, _ in _mem:
        a = agg.setdefault(
            m,
            {"model": m, "calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0},
        )
        a["calls"] += 1
        a["input_tokens"] += i
        a["output_tokens"] += o
        a["cost_usd"] += c
    return list(agg.values())