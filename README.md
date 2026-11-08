# BUILDWISE – Construction Worker Assignment System

BUILDWISE is an academic rule-based construction worker assignment application. It uses SWI-Prolog deductive reasoning to evaluate worker eligibility for tasks based on skills, experience, certifications, and availability.

## Technologies

- Python (Tkinter GUI)
- SWI-Prolog (reasoning engine)
- PySwip (Python–Prolog integration)
- SQLite (persistent worker and task records)

## Features

- Create, view, update, and delete worker and task records
- Check worker eligibility for a selected task
- Find eligible workers for a task
- Recommend suitable tasks for a worker
- Store records locally using SQLite

## Getting started

1. Install Python and SWI-Prolog, ensuring SWI-Prolog is available to PySwip.
2. Install Python dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Start the application:

   ```bash
   python gui_crud.py
   ```

The application stores local records in `construction.db` (excluded from Git). Check the application's database-initialization behavior before using a fresh installation.

## Screenshot

After adding a screenshot at `screenshots/buildwise-gui.png`, it can be displayed here:

<!-- ![BUILDWISE interface](screenshots/buildwise-gui.png) -->

## Project context

MSc Artificial Intelligence academic project demonstrating symbolic AI, knowledge representation, and deductive reasoning.
