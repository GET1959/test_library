# test_library

Приложение реализовано в соответствии с 
техзаданием https://docs.google.com/document/d/17qE_QawFOssdRIaEBzTaN8N-SYmkhh7tdNOy3ZTwHz8/edit?tab=t.0

Для запуска приложения необходимо:

1. Создать файл .env в соответствии с файлом .env.sample
2. Запустить контейнер в докере командой docker-compose up -d
3. Подключиться к базе данных, используя переменные из файла .env
4. Применить миграции командой alembic upgrade head
5. Запустить приложение командой uvicorn app.main:app --reload

Документация будет доступна по адресу http://127.0.0.1:8000/docs/