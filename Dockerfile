# Stage 1: Build frontend
FROM node:22-slim AS frontend-build
WORKDIR /app/classic-car-ui
COPY classic-car-ui/package.json classic-car-ui/package-lock.json ./
RUN npm ci
COPY classic-car-ui/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Copy built frontend into static directory
COPY --from=frontend-build /app/classic-car-ui/dist ./static

COPY start.sh ./
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
