FROM python:3.9.19-alpine3.20
WORKDIR /code
EXPOSE 8000
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "app"]