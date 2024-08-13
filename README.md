# Finances - By Isaac Norman

This readme is just a placeholder of enough info to know what this repo is and run it with sample data.

# About

I had a spreadsheet for a long time that I kept all my personal finances in.  It was good, but I always found it annoying to keep up to date, copying and pasting stuff in.  Also, with my excel skills at least, it didn't really scale well if I wanted to make a new visualisation or remap data.

I finally had a bit of time and thought I would kill two birds with one stone:  replace the spreadsheet with a nice app and also create a project that demonstrated my skills.

I have managed to create an app that should replace the spreadsheet.  However, it's taken a lot longer than I really had time for and it's the opposite of polished code I'd love to show off.  I'm mostly a backend developer and a LOT of this work was front end.  One day I'll make the code nice but that's not now, so no judging.

# What does it do?

Basically you can ingest different data files - ofx, csv - and build up a database of accounts, transactions and data points (currently about job/salary/tax) and then view it all in a web front end.

## Features
- Summary Page
  - Balance over time
  - Wealth pie chart
  - Stacked account bar chart (accounts summed over time)
- Accounts Page
  - View all accounts and navigate to Account Details
- Account Details Page
  - List of monthly transactions (like on your banking app)
  - Balance over time
  - value vs contributions for account types that grow such as share ISAs, houses etc.
  - link to account login (i.e. your banking web page)
- Taxable Income Page
  - visualisations on tax, income, salary and career
- General Features
  - Interpolation of missing transactional data (i.e. if you only have the odd value of a pension/asset it will work out the missing values)
  - All filterable by account type and time range

# What is incomplete?
- The code is extremely prototype - was rushed to just get functional.
- Most of the ingest currently happens via python, the UI for this needs implementing
- Editing accounts and manually inputing transactions
- A proper packed build of the front and back end
- A proper docker image for the front and back end
- Tests are basically a skeleton.  They need writing around the sample data.
- Plus lots more

# What's the architecture?

Backend: Python FastAPI, SqlAlchemy, Pydantic, Alembic
Frontend: Vue 3, Vuetify 3, TypeScript
DB: Dockerised Postgres

# How do I run it?

I will in future build both the front and backend and include in docker images, but for now:

- check out the code
- create a python venv and install the requirements.txt
- run the docker compose:
```
docker compose up -d
```
- initialise the db with alembic:
```
alembic upgrade head
```
- optionally load some sample data (recommend if you want to just give it a quick try)
```
python load_sample_data.py
```
- run the backend
```
fastapi dev backend/main.py
```
- install deps for the frontend
```
cd frontend
npm install
```
- run the frontend
```
cd frontend
npm run dev
```
- navigate to the frontend web address: http://localhost:3000/
- if you want to erase the db and start again
```
docker compose down db
docker volume rm finances_db
docker compose up db -d
```