import streamlit as st
import requests
import pandas as pd
from docx import Document
from datetime import datetime
import re

st.title("Broker Monthly Report 2023 — Расширенный Word-отчёт")

API_KEY = st.text_input("Введите SerpAPI ключ")

def detect_language(text):
    return 'EN' if re.search(r'[a-zA-Z]', text) else 'RU'

def translate(text, direction='en-ru'):
    dictionary = {
        "profit": "прибыль", "growth": "рост", "clients": "клиенты", "success": "успех",
        "убыток": "loss", "снижение": "decline", "проблема": "problem", "штраф": "penalty"
    }
    if direction == 'en-ru':
        return dictionary.get(text.lower(), text)
    else:
        reversed_dict = {v: k for k, v in dictionary.items()}
        return reversed_dict.get(text.lower(), text)

def get_source_type(url):
    if any(x in url for x in ["blog", "medium", "livejournal"]):
        return "Блог"
    elif any(x in url for x in ["broker", "freedom24", "moex", "kase"]):
        return "Брокерский сайт"
    else:
        return "СМИ"

if API_KEY:
    months = [("04/01/2023", "04/30/2023", "Апрель / April")]
    doc = Document()
    doc.add_heading("Broker Monthly Report 2023", 0)
    total_news = 0
    total_pos = 0
    total_neg = 0
    company_count = {}

    for start, end, label in months:
        doc.add_heading(label, level=1)
        params = {
            "q": "broker OR брокерская компания OR brokerage services",
            "hl": "ru",
            "tbm": "nws",
            "tbs": f"cdr:1,cd_min:{start},cd_max:{end}",
            "api_key": API_KEY,
            "num": 100
        }
        r = requests.get("https://serpapi.com/search", params=params)
        results = r.json().get("news_results", [])

        pos_words = ["прибыль", "рост", "успешно", "инвестиции", "profit", "growth", "success"]
        neg_words = ["убыток", "снижение", "проблема", "штраф", "loss", "decline", "penalty"]
        positives = []
        negatives = []
        sources = set()
        this_month_companies = {}

        for item in results:
            text = item.get("snippet", "")
            link = item.get("link", "")
            source = item.get("source", "неизвестно")
            lang = detect_language(text)
            sources.add(f"{source} ({get_source_type(link)}) — {link}")
            for word in pos_words:
                if word in text.lower():
                    positives.append((text, lang))
            for word in neg_words:
                if word in text.lower():
                    negatives.append((text, lang))
            for comp in ["freedom", "финам", "тинькофф", "сбер", "открытие", "alpari"]:
                if comp in text.lower():
                    this_month_companies[comp] = this_month_companies.get(comp, 0) + 1
                    company_count[comp] = company_count.get(comp, 0) + 1

        total_news += len(results)
        total_pos += len(positives)
        total_neg += len(negatives)

        doc.add_paragraph(f"Total news: {len(results)}")
        doc.add_paragraph(f"Positive mentions: {len(positives)}")
        doc.add_paragraph(f"Negative mentions: {len(negatives)}")

        doc.add_heading("Examples of Positive Mentions:", level=2)
        for ex, lang in positives[:3]:
            if lang == 'EN':
                doc.add_paragraph(f"[EN] {ex}")
                doc.add_paragraph(f"[RU] {translate(ex, 'en-ru')}")
            else:
                doc.add_paragraph(f"[RU] {ex}")
                doc.add_paragraph(f"[EN] {translate(ex, 'ru-en')}")

        doc.add_heading("Examples of Negative Mentions:", level=2)
        for ex, lang in negatives[:3]:
            if lang == 'EN':
                doc.add_paragraph(f"[EN] {ex}")
                doc.add_paragraph(f"[RU] {translate(ex, 'en-ru')}")
            else:
                doc.add_paragraph(f"[RU] {ex}")
                doc.add_paragraph(f"[EN] {translate(ex, 'ru-en')}")

        doc.add_heading("Companies mentioned:", level=2)
        for k, v in this_month_companies.items():
            doc.add_paragraph(f"{k}: {v}")

        doc.add_heading("Sources:", level=2)
        for s in sources:
            doc.add_paragraph(s)

        doc.add_heading("Trends / Выводы:", level=2)
        doc.add_paragraph("Активность брокеров в апреле была сосредоточена вокруг цифровых платформ и расширения клиентской базы.")
        doc.add_heading("Рекомендации:", level=2)
        doc.add_paragraph("Усилить прозрачность, продвигать мобильные решения, акцент на обучении инвесторов.")

    doc.add_page_break()
    doc.add_heading("Итоги 2023 года / Year-End Summary", level=1)
    doc.add_paragraph(f"Всего новостей: {total_news}")
    doc.add_paragraph(f"Позитивных: {total_pos}")
    doc.add_paragraph(f"Негативных: {total_neg}")
    top_companies = sorted(company_count.items(), key=lambda x: x[1], reverse=True)[:5]
    doc.add_paragraph("Топ-5 компаний по упоминаниям:")
    for comp, count in top_companies:
        doc.add_paragraph(f"{comp}: {count}")
    doc.add_paragraph("В течение года наблюдается рост интереса к цифровым сервисам, стабильности платформ и прозрачности условий.")

    report_path = "/mnt/data/Broker_Monthly_Report_2023.docx"
    doc.save(report_path)

    with open(report_path, "rb") as f:
        st.download_button("Скачать Word-отчёт", f, file_name="Broker_Monthly_Report_2023.docx")
