FROM python:3.12-slim
WORKDIR /app
COPY server.py tracker.js dashboard.html index.html demo.html ./
ENV PYTHONUNBUFFERED=1
ENV ANALYTICS_BIND=0.0.0.0
ENV ANALYTICS_PORT=8790
ENV ANALYTICS_DB=/var/data/analytics.sqlite
EXPOSE 8790
CMD ["python", "server.py"]
