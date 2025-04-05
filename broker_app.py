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

st.title("Глобальный анализ новостей о брокерах / Global Broker News Analysis (2023)")

API_KEY = st.text_input("Введите ваш SerpAPI ключ / Enter your SerpAPI Key:")

if API_KEY:
    queries = [
        ("брокер OR брокерская компания OR брокерские услуги", "ru"),
        ("broker OR brokerage firm OR brokerage services", "en")
    ]

    base_url = "https://serpapi.com/search"
    headers = {"Accept": "application/json"}

    months = [
        ("01/01/2023", "01/31/2023"),
        ("02/01/2023", "02/28/2023"),
        ("03/01/2023", "03/31/2023"),
        ("04/01/2023", "04/30/2023"),
        ("05/01/2023", "05/31/2023"),
        ("06/01/2023", "06/30/2023"),
        ("07/01/2023", "07/31/2023"),
        ("08/01/2023", "08/31/2023"),
        ("09/01/2023", "09/30/2023"),
        ("10/01/2023", "10/31/2023"),
        ("11/01/2023", "11/30/2023"),
        ("12/01/2023", "12/15/2023")
    ]

    all_news = []

    for query, lang in queries:
        for start, end in months:
            params = {
                "q": query,
                "hl": lang,
                "tbm": "nws",
                "tbs": f"cdr:1,cd_min:{start},cd_max:{end}",
                "api_key": API_KEY,
                "num": 100
            }
            response = requests.get(base_url, params=params, headers=headers)
            results = response.json()

            for news in results.get("news_results", []):
                title = news.get("title")
                link = news.get("link")
                snippet = news.get("snippet", "")
                source = news.get("source", "")
                date_str = news.get("date", "")
                try:
                    news_date = pd.to_datetime(date_str, dayfirst=True, errors='coerce')
                except:
                    news_date = None

                if news_date:
                    all_news.append({
                        "Источник / Source": source,
                        "Заголовок / Title": title,
                        "Ссылка / Link": link,
                        "Описание / Snippet": snippet,
                        "Дата / Date": news_date.date()
                    })

    df = pd.DataFrame(all_news)

    if not df.empty:
        st.subheader("Найденные глобальные новости / Global Broker News")
        st.dataframe(df)

        all_text = " ".join(df["Описание / Snippet"].tolist()).lower()
        tokens = nltk.word_tokenize(re.sub(r'[^а-яА-Яa-zA-Z]', ' ', all_text))
        stop_words = set(stopwords.words('russian')) | set(stopwords.words('english'))
        filtered_tokens = [word for word in tokens if word not in stop_words and len(word) > 2]

        word_freq = Counter(filtered_tokens).most_common(15)

        positive_words = ["рост", "успешно", "прибыль", "увеличение", "инвестиции", "growth", "profit", "investment", "success"]
        negative_words = ["убыток", "снижение", "проблема", "отказ", "штраф", "loss", "decline", "problem", "penalty"]
        pos_count = sum(all_text.count(w) for w in positive_words)
        neg_count = sum(all_text.count(w) for w in negative_words)

        companies = ["freedom", "финам", "тинькофф", "атфбанк", "halyk", "сбер", "открытие", "alpari", "interactive brokers"]
        df_mentions = pd.DataFrame(columns=["Компания / Company", "Дата / Date", "Упоминаний / Mentions"])

        for company in companies:
            for idx, row in df.iterrows():
                text = row["Описание / Snippet"].lower()
                count = text.count(company)
                if count > 0:
                    df_mentions.loc[len(df_mentions)] = [company, row["Дата / Date"], count]

        st.subheader("Часто встречающиеся слова / Frequent Words")
        words, counts = zip(*word_freq)
        fig1, ax1 = plt.subplots()
        sns.barplot(x=list(words), y=list(counts), ax=ax1)
        plt.xticks(rotation=45)
        st.pyplot(fig1)

        st.subheader("Оценка тональности / Sentiment Estimate")
        fig2, ax2 = plt.subplots()
        sns.barplot(x=["Позитив / Positive", "Негатив / Negative"], y=[pos_count, neg_count], palette="coolwarm", ax=ax2)
        st.pyplot(fig2)

        if not df_mentions.empty:
            df_mentions["Дата / Date"] = pd.to_datetime(df_mentions["Дата / Date"])
            st.subheader("Упоминания компаний по времени / Company Mentions Over Time")
            fig3, ax3 = plt.subplots()
            sns.lineplot(data=df_mentions, x="Дата / Date", y="Упоминаний / Mentions", hue="Компания / Company", marker="o", ax=ax3)
            plt.xticks(rotation=45)
            st.pyplot(fig3)
        else:
            st.info("Недостаточно данных для отображения упоминаний компаний / Not enough data for mentions chart.")
    else:
        st.warning("Новости не найдены / No news found.")
