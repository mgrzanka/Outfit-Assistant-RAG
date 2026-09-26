from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types

from src.config import Config
from src.services.chat.agents.root_orchestrator import create_root_orchestrator


class ChatService:
    def __init__(self) -> None:
        self._session_service = DatabaseSessionService(db_url=Config.DATABASE_URL)
        self._root_agent = create_root_orchestrator()

    async def perform_prompt(self, userId: str, user_input: str):
        session, runner = await self._get_session_and_runner(userId)

        input_message = types.Content(role="user", parts=[types.Part(text=user_input)])

        response = "Something went wrong and I can't answer your question :<"

        for event in runner.run(
            user_id=userId, session_id=session.id, new_message=input_message
        ):
            if event.is_final_response() and event.author == "outfit_presenter":
                if event.content and event.content.parts:
                    response = event.content.parts[0].text
                elif event.actions and event.actions.escalate:
                    response = f"Agent escalated: {event.error_message or 'No specific message.'}"
                break

        return response

    async def _get_session_and_runner(self, userId: str):
        existing_sessions = await self._session_service.list_sessions(
            user_id=userId, app_name=Config.APP_NAME
        )

        if len(existing_sessions.sessions) > 0 and existing_sessions.sessions[0]:
            session = existing_sessions.sessions[0]
        else:
            session = await self._session_service.create_session(
                app_name=Config.APP_NAME,
                user_id=userId,
            )

        runner = Runner(
            agent=self._root_agent,
            app_name=Config.APP_NAME,
            session_service=self._session_service,
        )

        return session, runner
