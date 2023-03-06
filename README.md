# Project - Predicting Electricity Demand in NY with Serverless

This is a project to test Serverless capability.
As features, the project uses historical daily demand, daily average temperature (celsius), and whether the date was a US Federal holiday or not.

Training data consists of the years 2017 - 2021. The data for historical daily demand is obtained from US Energy Information Administration (EIA) (Link to API) and the data for historical average daily temperature is obtained from National Oceanic and Atmospheric Administration (NOAA). The US Federal holidays are obtained from the USFederalHolidayCalendar library in pandas.tseries.holiday. The temperature data for the daily scheduled batch predictions is obtained from WeatherAPI.

Along with the model's predictions we also provide the forecasted demand from EIA and find that our model's predicted values turn out to be fairly close to those of the official EIA forecast.
