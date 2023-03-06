import modal

LOCAL = False



def feature_elec():
    import pandas as pd
    from pandas.tseries.holiday import USFederalHolidayCalendar as calendar
    import datetime
    import requests
    import hopsworks
    import os
    
    os.environ['EIA_API_KEY'] = "4goTb0VNLmTBcF4hd6VyD1BHsJNcgA6ufRW4R6ax"
    os.environ['WEATHER_API_KEY'] = "73796406bbcb40af8d121354230303"
    os.environ['HOPSWORKS_API_KEY'] = "Xs12h5FlAi5pkOJx.p7N2lXzfEEWvOZ96X3CaAn46mtKpWMmVGRymNzaCtpt4eAhUny8ERaLjwx0OOjri"
    
    # Get date 2 days ago (Demand and demand forecast are 2 days behind)
    prediction_date = datetime.datetime.today() - datetime.timedelta(days=2)
    prediction_date = prediction_date.date()
    print("Date: {}".format(prediction_date))
    
    url = ('https://api.eia.gov/v2/electricity/rto/daily-region-data/data/'
           '?frequency=daily'
           '&data[0]=value'
           '&facets[respondent][]=NY'
           '&facets[timezone][]=Eastern'
           '&facets[type][]=D'
           '&facets[type][]=DF'
           '&sort[0][column]=period'
           '&sort[0][direction]=desc'
           '&offset=0'
           '&length=5000')
    url = url + '&start={}&end={}&api_key={}'.format(prediction_date, prediction_date, os.environ.get('EIA_API_KEY'))
    data = requests.get(url).json()['response']['data']
    
    data_demand = data[1]
    data_demand = pd.DataFrame(data_demand, index=[0])
    
    # Clean DF to same format as fg
    data_demand = data_demand[['period', 'value']].rename(columns={'period': 'date', 'value': 'demand'})
    data_demand['date'] = pd.to_datetime(data_demand['date'], infer_datetime_format=True)
    print("EIA Demand data: \n{}".format(data_demand.head()))

    # Get temperature for date
    weather_api_key = os.environ.get('WEATHER_API_KEY')
    weather_url = ('http://api.weatherapi.com/v1/history.json'
                   '?key={}'
                   '&q=New%20York,%20USA'
                   '&dt={}').format(weather_api_key, prediction_date)
    
    weather_data = requests.get(weather_url).json()['forecast']['forecastday'][0]['day']['avgtemp_c']
    weather_df = pd.DataFrame({'date': [prediction_date], 'temperature': [weather_data]})
    weather_df['date'] = pd.to_datetime(weather_df['date'], infer_datetime_format=True)
    print("Weather data: \n{}".format(weather_df))
    
    # Add month/day features
    merged_df = pd.merge(weather_df, data_demand, how='inner', on='date')
    merged_df['day'] = merged_df['date'].dt.dayofweek
    merged_df['month'] = merged_df['date'].dt.month
    
    # Get bank holidays
    holidays = calendar().holidays(start=merged_df['date'].min(), end=merged_df['date'].max())
    merged_df['holiday'] = merged_df['date'].isin(holidays).astype('int32')
    print("Combined data: \n{}".format(merged_df.head()))
    
    project = hopsworks.login()
    fs = project.get_feature_store()
    
    fg = fs.get_feature_group(name="ny_elec", version=1)
    fg.insert(merged_df, write_options={"wait_for_job": False})
    
if not LOCAL:
    stub = modal.Stub()
    image = modal.Image.debian_slim().apt_install(["libgomp1"]).pip_install(["hopsworks==3.0.4", "seaborn", "joblib", "scikit-learn==1.0.2", "xgboost==1.5", "dataframe-image", "pandas",
        "datetime", "requests", "python-dotenv"])
        
    @stub.function(image=image, schedule=modal.Period(days=1), secret=modal.Secret.from_name("HOPSWORKS_API_KEY"))
    def modal_feature_elec():
        feature_elec()
        

if __name__ == "__main__":
    if LOCAL:
        feature_elec()
    else:
        stub.deploy("modal_feature_elec")
    