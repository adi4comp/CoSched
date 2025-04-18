FROM python:3.9-slim


WORKDIR /app



COPY . .

RUN pip install --no-cache-dir -r requirements.txt


ENV PYTHONPATH=/app/src/:$PYTHONPATH


RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

CMD [ "bash" ]
