gcloud builds submit --tag gcr.io/groupmaker-314159/qrmake
gcloud run deploy --image gcr.io/groupmaker-314159/qrmake --platform managed


