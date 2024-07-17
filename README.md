# Finance Forecaster
This cloud-based project automates the collection, storage, and analysis of daily stock and cryptocurrency data. Two Azure Functions fetch data daily from external APIs and web scraping, storing it in an Azure SQL Server database. A third function uses LightGBM to generate 14-day predictions, which are then visualized in interactive dashboards using Power BI


# Project Structure
![Project Structure][project_structure]

[project_structure]: ./project_structure.png
