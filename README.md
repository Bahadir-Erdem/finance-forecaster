<a id="readme-top"></a>

## Table of Contents

- [Finance Forecaster](#finance-forecaster)
- [Dashboard](#dashboard)
- [Project Structure](#project-structure)
- [Database ER Diagram](#database-er-diagram)
- [Lightgbm Performance Metrics](#lightgbm-performance-metrics)

# Finance Forecaster

This cloud-based project automates the collection, storage, and analysis of daily stock and cryptocurrency data. Two Azure Functions fetch data daily from external APIs and web scraping, storing it in an Azure SQL Server database. A third function uses LightGBM to generate 14-day predictions, which are then visualized in interactive dashboards using Power BI.

Because of vCore limitations on Azure SQL Database, can only take 5 coin data and 5 stock data.

## To Use The Dashboard
You may need to refresh the data for every data object

## To Use The Project
* You need to fill the "azure_sql_server" variable inside database_config.yaml.
* You need to fill every variable of data sources inside database_config.yaml.
* You need to make connections with Azure SQL Database inside Power BI file.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Dashboard

![MSFT][msft]

![AAPL][aapl]

![Bitcoin][bitcoin]

![Etherium][etherium]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Project Structure

![Project Structure][project_structure]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Database ER Diagram

![ER Diagram][er_diagram]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Lightgbm Performance Metrics

For every entity(AAPL, Bitcoin etc.); predictionss made for 14 days into the future and for every value MAE(Mean Absolute Error), RMSE(Root Mean Squared Error) and sMAPE(Symmetric mean absolute percentage error) metrics calculated after that all values averaged for the same entity. Finally all metric values averaged. 

These are the final results:

![LightGBM Performance][lightgbm_performance]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

[project_structure]: images/project_structure.png
[er_diagram]: images/er_diagram.png
[aapl]: images/aapl.png
[msft]: images/msft.png
[bitcoin]: images/bitcoin.png
[etherium]: images/etherium.png
[lightgbm_performance]: images/lightgbm_performance.png