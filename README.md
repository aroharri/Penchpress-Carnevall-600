# Penchpress Carnevall 600

**The first version of Penkkikarnevaalit — a Streamlit prototype backed by Google Sheets.**

A group of friends set a shared goal: 600 kg of combined estimated one-rep max
on the bench press. This app was built to track it. Everyone logs their sets,
the app estimates a one-rep max with the Brzycki formula, and the squad's
combined total is measured against the goal.

## What it does

- **The Path to 600** — combined 1RM against the target, over time
- **Squad Roster** — each lifter's current estimate and progress
- **Feed** — a running log of what the group has lifted
- **Logging** — pick a weight, pick reps, submit

## How it is built

| | |
|---|---|
| UI | Streamlit |
| Charts | Plotly |
| Data | Pandas |
| Storage | Google Sheets — read as CSV via the gviz export, written through an Apps Script webhook |

Roughly 470 lines in a single `app.py`. The product and its analytics live in
the same file, which is exactly what a prototype is for.

## Why it still exists

This is where the idea was proven, and it is kept as the first step rather than
deleted. It answered the questions that mattered before anything was built
properly: is the Brzycki estimate good enough to motivate people, does a shared
goal change how often the group trains, and is a feed worth the effort.

It also showed where the design would not hold. Google Sheets has no schema, no
constraints and no concurrency story — two people logging at once was a real
problem, not a theoretical one. Every metric was recomputed inline on each page
render, so the product and its reporting could never be changed independently.

## What came after

The current version is a separate React application on Supabase, with a
Postgres schema, real authentication and a social layer.

Analytics moved out into its own project:

**[penkkikarnevaalit-analytics](https://github.com/aroharri/penkkikarnevaalit-analytics)**
— an ELT pipeline over two sources (Supabase and the Open-Meteo weather API)
into DuckDB, transformed with dbt across three model layers, orchestrated with
Dagster, and reconciled figure by figure against what the application shows its
users.

That split is the lesson this prototype taught: when the product computes its
own numbers inline, nobody can check them.

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Requires a `.streamlit/secrets.toml` with the Google Sheets connection and the
Apps Script URL. Not included.
