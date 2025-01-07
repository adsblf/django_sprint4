# Blogicum

Выполнил студент ОмГТУ, группы ИВТ-223 Бережнов А.Д.

## Запуск проекта:

* Клонировать репозиторий или скачать его архивом: 
        ```
        git clone <SSH>
        ```
     Перейти в папку проекта
        ```
        cd django_sprint4
        ```
* Создать и запустить виртуальное окружение:
        ```
        python -m venv venv
        ```
        ```
        .\venv\Scripts\activate
        ```
* Установить зависимости из файла requirements.txt:
        ```
        pip install -r requirements.txt
        ```
* Применить все миграции к БД:
        ```
        python blogicum\manage.py migrate
        ```
* Загрузить данные из БД db.json в БД в проекте Django:
        ```
        python blogicum\manage.py loaddata db.json
        ```
* Запустить сервер с проектом: 
        ```
        python blogicum\manage.py runserver
        ```
