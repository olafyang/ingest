FROM python:latest

RUN pip install Pillow

WORKDIR /app
COPY compressor.py .

ENTRYPOINT [ "python3", "compressor.py" ]