from newsapi import NewsApiClient
import pandas as pd
from datetime import datetime, timedelta
import statistics
import google.auth
from google.cloud import language_v1 as language
import os


class StockNews:
    def __init__(self) -> None:
        path = os.getcwd()
        print(path)
        # self.apiKey = "d8374c4ebc1f49c9bcf9c1b89df7c65a" # Jim
        # self.apiKey = "695420fc828541cb8b3b3589c778a226" # Bilal
        self.apiKey = "ed5bb80dde3d432da44a675baeb164c9"  # Clay
        self.newsapi = NewsApiClient(api_key=self.apiKey)
        self.credentials, project_id = google.auth.load_credentials_from_file(path + "\GoogleCreds.json")
        self.newsArticles = None
        self.client = language.LanguageServiceClient(credentials=self.credentials)

    def getNewsArticles(self, topic, count, pastDays):
        today = datetime.today()
        pastDays = datetime.today() - timedelta(days=pastDays)

        headlines = self.newsapi.get_everything(q=topic,
                                                qintitle=topic,
                                                from_param=pastDays,
                                                to=today,
                                                sort_by="popularity",
                                                language='en',
                                                page_size=count
                                                )

        df = pd.DataFrame(headlines["articles"])
        self.newsArticles = df[["title", "description", "url"]]

        return self.newsArticles

    def getSentiment(self, text):
        doc = language.Document(content=text, language='en', type_=language.Document.Type.PLAIN_TEXT)
        textSentiment = self.client.analyze_sentiment(
            document=doc,
            encoding_type='UTF32'
        )
        SentimentScore = textSentiment.document_sentiment.score
        return SentimentScore

    def get_sentiment_score(self):
        sentiment = []
        for desc in self.newsArticles['description']:
            sentiment.append(self.getSentiment(desc))
        score = statistics.mean(sentiment)
        if score > 0:
            rating = 'Positve Sentiment'
        else:
            rating = 'Negative Sentiment'

        score = score * 100
        # print(rating)
        # print(score)
        return rating, round(score, 1)
