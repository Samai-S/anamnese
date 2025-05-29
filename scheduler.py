import os.path
import datetime as dt
import pytz
import json # Para imprimir o JSON de forma legível

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def google_calendar_scheduler():
    # ---------- autenticação ----------
    creds = None
    if os.path.exists("./config/token.json"):
        creds = Credentials.from_authorized_user_file("./config/token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("./config/credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("./config/token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        tz_name = "America/Sao_Paulo"
        local_tz = pytz.timezone(tz_name)

        first_dose_start_utc = dt.datetime.utcnow() + dt.timedelta(hours=3)
        first_dose_start_local = first_dose_start_utc.replace(tzinfo=dt.timezone.utc).astimezone(local_tz)
        
        dose_duration = dt.timedelta(minutes=30)
        first_dose_end_local = first_dose_start_local + dose_duration

        total_doses = 20

        # ---------- montar RRULE ----------
        rrule_line = f"RRULE:FREQ=HOURLY;INTERVAL=6;COUNT={total_doses}"

        # ---------- Preparar dateTime strings sem microssegundos ----------
        # Isso às vezes ajuda com APIs mais sensíveis ao formato ISO
        dt_start_iso = first_dose_start_local.replace(microsecond=0).isoformat()
        dt_end_iso = first_dose_end_local.replace(microsecond=0).isoformat()

        # ---------- criar evento ----------
        event_body = {
            "summary": "Tomar Dipirona",
            "description": "Dipirona 500 mg – dose de 6 em 6 h por 5 dias.",
            "start": {
                "dateTime": dt_start_iso, # Usando string sem microssegundos
                "timeZone": tz_name,
            },
            "end": {
                "dateTime": dt_end_iso,   # Usando string sem microssegundos
                "timeZone": tz_name,
            },
            "recurrence": [rrule_line],
            "attendees": [{"email": "sucosucosucosucosuco123@gmail.com"}],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 10},
                    {"method": "popup", "minutes": 10},
                ],
            },
        }

        # --- DEBUG ---
        print("--- INFORMAÇÕES DE DEBUG ---")
        print(f"Linha RRULE Gerada: '{rrule_line}'")
        print(f"Start dateTime (ISO): {dt_start_iso}")
        print(f"End dateTime (ISO): {dt_end_iso}")
        print(f"Timezone: {tz_name}")
        print("Corpo do Evento Completo (JSON):")
        print(json.dumps(event_body, indent=2, ensure_ascii=False)) # ensure_ascii=False para acentos
        print("--- FIM DAS INFORMAÇÕES DE DEBUG ---")
        # --- FIM DEBUG ---
        
        created_event = service.events().insert(
            calendarId="primary",
            body=event_body,
            sendUpdates="all"
        ).execute()

        print("Série de eventos recorrentes criada! Link:", created_event.get("htmlLink"))

    except HttpError as error:
        print("Erro na API Calendar:", error)
        # Imprimir detalhes do erro se disponíveis no objeto de erro
        # O atributo _get_reason() é interno, mas pode ter a mensagem. error.reason é público
        # error.content geralmente tem o JSON da resposta de erro
        print("Detalhes do erro (error.content):", error.content.decode() if isinstance(error.content, bytes) else error.content)
    except Exception as e:
        print(f"Ocorreu um erro geral: {e}")

if __name__ == "__main__":
    if not os.path.exists("./config"):
        os.makedirs("./config")
    google_calendar_scheduler()