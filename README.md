# Database API PoC

## Introduction

This repository contains a simple PoC of an API to execute ad-hoc data requests against a database of business reviews. The following sections will explain how to run the PoC locally, its architecture, and how to use the API itself.

## Prerequisites

- [Docker](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install) (included in Docker Desktop)
- Python 3.12 or higher

## Getting Started

### 1. Deploy Database and API

First we need to create a secret database password. Docker Compose will look for a file called `db_password.txt` in a folder called `secrets`:

```bash
# Create the secrets folder in the root of the repository
mkdir secrets
# Create a file containing your database password
echo "YOUR-SUPER-SECRET-PASSWORD" > secrets/db_password.txt
```

Use Docker Compose to deploy all the necessary infrastructure to run the PoC. In the root directory run:

```bash
docker-compose up -d
```

This will create the following application:

![Figure 1: Solution Architecture](./docs/architecture.drawio.png)

Will also initialize the database with tables and schemas

### 2. Initialize and Populate Database Schema and Tables

To test our API we need to load the data from the `tp_reviews.xlsx` into the database. A helper script takes care of that. You can find it under `src/init/init.py`. To execute it, run the following commands in a terminal from the root directory of this repository:

```bash
# Create a new virtual environment
python -m venv .venv
# Activate it
source .venv/bin/activate
# Install (development) requirements
pip install -r requirements.txt
# Execute the init script
python src/init/init.py
```

The script loads the Excel file with data and converts the denormalized table into three separate tables to reflect a more realistic database setup. We're left with a simple star schema with a facts table (`reviews`) and two dimension tables (`reviewers` and `businesses`). The `reviews` table has foreign keys to the other two tables. Additionally a view (`review_details`) is created by (re)joining the reviews data to allow for simpler API queries of more detailed review data. The schema is also visualized below:

![Figure 2: Database Schema](./docs/schema.drawio.png)

## Usage

For a complete API specification go to the APIs docs at http://localhost:8000/docs.

### Examples

Provide reviews for business X (e.g. "Artisan Coffee Roasters"):

```
http://localhost:8000/reviews?business_name=Artisan%20Coffee%20Roasters
```

Provide reviews by user Y (e.g. "David Knox"):

```
http://localhost:8000/reviews?user_name=David%20Knox
```

Provide user account information for user Z (e.g. "Sahra Barker"):

```
http://localhost:8000/users?name=Sarah%20Barker
```

## Developing

Contributions are welcome! Please follow these step to make sure you set up your local development correctly and adhere to the conventions followed in the project:

```bash
# Create a new virtual environment
python -m venv .venv
# Activate it
source .venv/bin/activate
# Install (development) requirements
pip install -r requirements.txt
```

The pre-commit hooks will automatically lint and format your code on commit as well as enforce branch naming conventions and semantic commit messages. It also runs security scans of your code and the projects unit tests. To install them run:

```bash
# Install the projects pre-commit hooks
pre-commit install --hook-type pre-commit --hook-type commit-msg
```

## FAQ

Q: Why use Docker Compose and not something more scalable like Kubernetes (k8s, k3s)?

A: This way it is easier to reproduce locally for anyone who wants to try it out, however, since everything is dockerized already, the `docker-compose.yaml` could easily be converted into k8s manifest files.

Q: Why use Docker instead of cloud services?

A: This could totally be built using cloud services e.g. on AWS with API Gateway, Lambda functions and a SQL Database such as Aurora Postgres or a NoSQL Database, such as DynamoDB. However, this makes it hard to reproduce and hard to migrate. Docker containers are cloud agnostic, also, I'm a cheapskate and don't want to pay for it.

Q: Why use Postgres as database?

A: Great question! The API does not require long running analytical queries but fast transactional ones, so an OLTP database works best in this case. Of all OLTP databases I have the most experience with Postgres, so I picked that.

Q: Why use FastAPI to design the API?

A: I love Python. FastAPI can with next to no changes be used for production scenarios (unlike e.g. Flask). It comes with automatic API documentation and can easily be unit tested with it's integrated testing framework.

Q: Did you use ChatGPT to build this?

A: Absolutely. I use LLMs in my daily work from ideation phase to code autocomplete (while constantly staying alert 👀). I use it for sparring and ask it how I could improve aspects of my code. In this case I actually went with my gut feeling regarding the overall architecture as I didn't like what the AI suggested (Flask/Django + SQLite). Individual scripts I normally initially draft using LLMs and then correct and adapt to my personal liking. In some cases I learn new things by retracing what the AI did (e.g. the Postgres docker image runs init SQL scripts when placed in the correct path, wow!).
