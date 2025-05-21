FROM mcr.microsoft.com/devcontainers/python:0-3.10

RUN apt-get update && apt-get install -y --no-install-recommends       git build-essential && rm -rf /var/lib/apt/lists/*

RUN pip install       langchain==0.2.0 langgraph==0.0.19 qdrant-client==1.9.1       duckdb spacy==3.7.4 "sentence-transformers==2.7.0"

RUN python -m spacy download en_core_web_sm