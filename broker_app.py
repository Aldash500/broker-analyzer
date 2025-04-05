import requests
import pandas as pd
from datetime import datetime
from collections import Counter
import nltk
import re
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

nltk.download('punkt')
nltk.download('stopwords')
from nltk.corpus import stopwords

st.title("Анализ новостей о брокерах (РФ и Казахстан)")

API_KEY = st.text_input("Введите ваш SerpAPI ключ:")

if API_KEY:
    query = "деятельность брокеров биржа Казахстан Россия"
    start_date = datetime(2023, 4, 1)
    end_date = datetime(2023, 12, 15)

    params = {
        "q": query,
        "hl": "ru",
        "gl": "ru",
        "tbm": "nws",
        "api_key": API_KEY,
        "num": 100
    }

    response = requests.get("https://serpapi.com/search", params=params)
    results = response.json()

    news_data = []
    for news in results.get("news_results", []):
        title = news.get("title")
        link = news.get("link")
        snippet = news.get("snippet", "")
        date_str = news.get("date", "")
        
        try:
            news_date = pd.to_datetime(date_str, dayfirst=True, errors='coerce')
        except:
            news_date = None

        if news_date and start_date <= news_date <= end_date:
            news_data.append({
                "Заголовок": title,
                "Ссылка": link,
                "Описание": snippet,
                "Дата публикации": news_date.date()
            })

    df = pd.DataFrame(news_data)

    if not df.empty:
        st.subheader("Найденные новости")
        st.dataframe(df)

        all_text = " ".join(df["Описание"].tolist()).lower()
        tokens = nltk.word_tokenize(re.sub(r'[^а-яА-Яa-zA-Z]', ' ', all_text))
        stop_words = set(stopwords.words('russian'))
        filtered_tokens = [word for word in tokens if word not in stop_words and len(word) > 2]

        word_freq = Counter(filtered_tokens).most_common(15)

        positive_words = ["рост", "успешно", "прибыль", "увеличение", "инвестиции"]
        negative_words = ["убыток", "снижение", "проблема", "отказ", "штраф"]
        pos_count = sum(all_text.count(w) for w in positive_words)
        neg_count = sum(all_text.count(w) for w in negative_words)

        companies = ["freedom", "финам", "тинькофф", "атфбанк", "halyk", "сбер", "открытие"]
        df_mentions = pd.DataFrame(columns=["Компания", "Дата", "Упоминаний"])

        for company in companies:
            for idx, row in df.iterrows():
                text = row["Описание"].lower()
                count = text.count(company)
                if count > 0:
                    df_mentions.loc[len(df_mentions)] = [company, row["Дата публикации"], count]

        st.subheader("Часто встречающиеся слова")
        words, counts = zip(*word_freq)
        fig1, ax1 = plt.subplots()
        sns.barplot(x=list(words), y=list(counts), ax=ax1)
        plt.xticks(rotation=45)
        st.pyplot(fig1)

        st.subheader("Оценка тональности новостей")
        fig2, ax2 = plt.subplots()
        sns.barplot(x=["Позитив", "Негатив"], y=[pos_count, neg_count], palette="coolwarm", ax=ax2)
        st.pyplot(fig2)

        if not df_mentions.empty:
            df_mentions["Дата"] = pd.to_datetime(df_mentions["Дата"])
            st.subheader("Упоминания компаний по времени")
            fig3, ax3 = plt.subplots()
            sns.lineplot(data=df_mentions, x="Дата", y="Упоминаний", hue="Компания", marker="o", ax=ax3)
            plt.xticks(rotation=45)
            st.pyplot(fig3)
        else:
            st.info("Недостаточно данных для отображения упоминаний компаний.")
    else:
        st.warning("Нет новостей за указанный период.")
