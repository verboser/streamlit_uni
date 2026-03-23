import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import datetime

st.title("Анализ температурных данных")

upl_file = st.file_uploader("Дайте свой файлик", type=["csv"])

if upl_file:
    df = pd.read_csv(upl_file)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    cities = df["city"].unique()
    selected_city = st.selectbox("Выберите город", cities)
    api_key = st.text_input("Введиет API-ключ от OpenWeatherMap (красть не буду, честно)", type="password")

    city_data = df[df["city"] == selected_city].copy()
    city_data["roll_mean"] = city_data["temperature"].rolling(window=30).mean()

    season_stats = city_data.groupby("season")["temperature"].agg(["mean", "std"]).reset_index()
    city_data = city_data.merge(season_stats, on="season")

    city_data["is_anomaly"] = (city_data["temperature"] < (city_data["mean"] - 2 * city_data["std"])) | \
                              (city_data["temperature"] > (city_data["mean"] + 2 * city_data["std"]))

    st.subheader("Описательная статистика")
    st.dataframe(city_data.describe())

    st.subheader("Временной ряд температур")
    fig_ts = px.scatter(city_data, x="timestamp", y="temperature", color="is_anomaly",
                        title=f"Температура в городе {selected_city}")
    fig_ts.add_scatter(x=city_data["timestamp"], y=city_data["roll_mean"], mode="lines", name="Скользящее среднее")
    st.plotly_chart(fig_ts)

    st.subheader("Сезонные профили")
    fig_season = px.bar(season_stats, x="season", y="mean", error_y="std",
                        title=f"Сезонные профили для {selected_city}")
    st.plotly_chart(fig_season)

    if api_key:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={selected_city}&appid={api_key}&units=metric"
        res = requests.get(url).json()

        if res.get("cod") != 200:
            st.error(res.get("message", "Invalid API key."))
        else:
            current_temp = res["main"]["temp"]
            st.write(f"Текущая температура: {current_temp} C")

            current_month = datetime.datetime.now().month
            month_to_season = {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring",
                               6: "summer", 7: "summer", 8: "summer", 9: "autumn", 10: "autumn", 11: "autumn"}
            current_season = month_to_season[current_month]

            season_data = season_stats[season_stats["season"] == current_season].iloc[0]
            mean_temp = season_data["mean"]
            std_temp = season_data["std"]

            if (current_temp < mean_temp - 2 * std_temp) or (current_temp > mean_temp + 2 * std_temp):
                st.warning("Текущая температура является НЕ адекватная для текущего сезона. (как я всю эту неделю перед сессией)")
            else:
                st.success("Текущая температура нормальная.")