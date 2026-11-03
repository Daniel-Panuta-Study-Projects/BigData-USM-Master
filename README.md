# Big Data — USM labs

| Folder | Contents |
|---|---|
| `Ex1/` | Introductory PySpark exercise on the MovieLens dataset (`movies.csv`, `ratings.csv`). |
| `Lab1/` | Exploring, processing and analysing NYC Citywide Payroll + Civil List data: PySpark, Kafka streaming, dashboard. |
| `Lab2/` | Databricks (Delta Lake, Spark MLlib model, backup, fault tolerance, monitoring) and a Power BI dashboard. |

## Running

- **Ex1:** `docker compose -f Ex1/compose.yaml up`, then open Jupyter at `http://localhost:8888`.
- **Lab1:** put `nyc_payroll_data.parquet` and `nyc_civil_list.parquet` from NYC Open Data ([Citywide Payroll](https://data.cityofnewyork.us/d/k397-673e), [Civil List](https://data.cityofnewyork.us/d/ye3c-m4ga); `upload_nyc_data.py` downloads one dataset through the API) into `Lab1/nyc-data/`, start Kafka with `docker compose -f Lab1/docker-compose.streaming.yml up -d` and run `Lab1/lab1.ipynb`.
- **Lab2:** import the notebooks into Databricks and run `lab2_databricks`. The report is `Lab2/predare/lab2_dashboard.pbix`.

Large data files and `data_lake/` are not in the repository; running Lab1 regenerates them.
