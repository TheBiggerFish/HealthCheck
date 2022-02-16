FROM python:3.8.10

COPY . /app
WORKDIR /app
RUN pip install --upgrade pip
RUN pip install -e .
RUN echo "Installation finished"


CMD ["python","src/main.py"]
