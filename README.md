# 🔎 Reddit Radar

**🚧 Work in Progress — Early Detection of Technology Trends from Reddit Communities**

---

## 📘 Overview

**Reddit Radar** is an end-to-end data analytics platform that monitors Reddit discussions to uncover emerging technology trends before they gain mainstream attention.

By analyzing thousands of Reddit posts from developer- and tech-focused communities, the platform provides early signals on:
- 🚀 New technology adoption
- 📈 Shifting developer sentiment
- 🔁 Cross-community trend propagation

---

## 🎯 Project Objectives

- **📊 Trend Detection**  
  Use TF-IDF to surface emerging technologies and niche topics gaining traction.

- **📉 Sentiment Tracking**  
  Monitor community sentiment on key topics to identify enthusiasm, skepticism, or fatigue.

- **🌐 Community Diffusion Mapping**  
  Visualize how ideas and technologies move from niche to general subreddits.

- **📈 Predictive Signals**  
  Identify "trend-leader" vs "trend-follower" communities to anticipate what's next.

---

## 🛠️ Tech Stack

| Layer              | Tools / Libraries                             |
|--------------------|-----------------------------------------------|
| **Data Collection** | Python, Reddit API (PRAW)                    |
| **Storage**         | DuckDB (in-process OLAP database)            |
| **Data Modeling**   | dbt Core (models in SQL, executed locally)   |
| **Analytics**       | TF-IDF, sentiment analysis (transformers, spaCy) |
| **Visualization**   | Streamlit (interactive dashboards)           |
| **Orchestration**   | GitHub Actions (scheduled runs every 6h)     |

---

## ✅ Project Status

### Completed
- [x] Architecture and planning
- [x] Core repository structure

### In Progress
- [ ] Reddit API integration and data collection
- [ ] DuckDB ingestion & schema design
- [ ] NLP pipeline (TF-IDF, sentiment scoring)
- [ ] dbt models (trends & sentiment over time)

### Upcoming
- [ ] Streamlit dashboard UI
- [ ] GitHub Actions for 6-hour refresh
- [ ] Trend spike alert system (email/webhook)
- [ ] Cross-subreddit propagation analysis

---

## 🚀 Expected Capabilities

Once complete, Reddit Radar will:

- Ingest **3,000+ posts daily** across 10+ subreddits
- Track **tech trends & developer sentiment in near real-time**
- Highlight **early-stage discussions** on upcoming tools and frameworks

---

## 🧪 Example Use Cases (Coming Soon)

- 🔍 Identify when a library like `LangChain` starts trending in niche ML subreddits
- 📉 Detect declining sentiment in developer discussions around a tool or language
- 🌱 Surface fast-growing topics not yet in mainstream tech media

---

## 🧰 Getting Started

> *Setup instructions will be added once initial modules are complete.*

Planned steps:
1. Clone repo and install dependencies
2. Add `.env` file with Reddit API keys
3. Run ingestion and processing pipeline locally or via Docker
4. Launch Streamlit dashboard to explore data

---

## 🧑‍💻 Contributing

This project is currently under solo development. Contributions may be welcomed once the MVP is released.


---

## 📌 Disclaimer

This project is under active development. Features, models, and documentation may change frequently.
