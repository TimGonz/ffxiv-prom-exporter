FROM python:3
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8808
ENTRYPOINT ["python"]
CMD ["FFXIVPromExporter.py"]