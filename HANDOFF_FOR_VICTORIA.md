1) Версия этапа: v0.4 (Repair + Self-Test Pack)

2) Ключевые изменения:
- Добавлен мастер-скрипт START_ALL.bat (проверка py -3.12, блок Python 3.14, авто .venv, deps, .env, запуск GUI, лог в logs/setup.log). Обновлён START_LAUNCHER.bat с тем же логом и проверками.
- GUI лаунчер усилен: вкладка «Диагностика» (инфо об окружении, кнопки проверки зависимостей, BOT_TOKEN через real getMe, OpenAI ping, открыть logs), улучшенный хэндлинг ошибок с выводом пути к logs/launcher.log.
- CLI: launch.py получил --selftest (tools/selftest.py), улучшенный вывод ошибок GUI. bot.py теперь логирует точную причину StartupError.
- Самотест tools/selftest.py проверяет Router/handlers, покрытие callback_data, prompt builder, QuotaService (SQLite).
- README обновлён: «2 клика», диагностика, запрет Python 3.14.

3) Как запускать на Windows 10:
- Двойной клик по START_ALL.bat. Если .env отсутствует — откроется в Notepad для вставки BOT_TOKEN. Лог: logs/setup.log.
- Запустить GUI вручную: START_LAUNCHER.bat (тот же лог). CLI: .venv\Scripts\python.exe launch.py --run-bot

4) Где смотреть логи и конфиг:
- logs/setup.log — батники/установка.
- logs/launcher.log — GUI.
- logs/app.log — бот.
- DB_PATH из .env (по умолчанию bot.db).

5) Обязательные проверки (в контейнере не выполнялись, нет Windows/py -3.12/OpenAI токенов):
- NOT VERIFIED HERE: START_ALL.bat (ожидаемо: создаёт .venv, ставит зависимости, открывает .env, запускает GUI).
- NOT VERIFIED HERE: python launch.py --selftest (ожидаемо: ALL TESTS PASSED).
- NOT VERIFIED HERE: python launch.py --print-env (ожидаемо: вывод с маскировкой токенов).
- NOT VERIFIED HERE: python launch.py --test-ai (stub или OpenAI, короткий ответ/ошибка).
- NOT VERIFIED HERE: при USE_OPENAI=true и валидном ключе: python launch.py --test-ai (ожидаемо: OpenAI ok либо явная ошибка 401/429).
- NOT VERIFIED HERE: при валидном BOT_TOKEN: python launch.py --run-bot, затем /start в Telegram отвечает (ожидаемо: меню и уведомление про stub при отсутствии OpenAI).

6) Примечания/риски:
- Python 3.14 намеренно блокируется; нужен py -3.12. В Linux/macOS запуск возможен вручную (python3.12), но батники рассчитаны на Windows.
- Проверки токена и зависимостей реальны (aiogram getMe, импорт модулей); требуют сети и корректных ключей на рабочей машине.
