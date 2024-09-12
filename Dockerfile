FROM python:3.11.9-slim
WORKDIR /code
EXPOSE 80
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "-m", "app"]