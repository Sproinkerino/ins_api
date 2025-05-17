import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .IlpAdvisor import ChatSession, ILPAdvisor

# one advisor instance for embedding/QA
advisor = ILPAdvisor()

@api_view(["POST"])
def chat(request):
    """
    Stateless chat endpoint expecting:
      - user_id:     string
      - session:     object|null  (the last state)
      - message:     string|null  (the user's latest reply)
    """
    payload    = request.data
    user_id    = payload.get("user_id")
    sess_state = payload.get("session")
    user_msg   = payload.get("message")

    if not user_id:
        return Response(
            {"detail": "Missing required field: user_id"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 1) Hydrate or start new ChatSession
    if sess_state is None:
        cs = ChatSession(advisor.REQUIRED_FIELDS, advisor.llm)
        assistant_msg = cs.start_chat()
        done = False
    else:
        cs = ChatSession(advisor.REQUIRED_FIELDS, advisor.llm)
        # restore previous state
        cs.answers        = sess_state["answers"]
        cs.follow_ups     = sess_state["follow_ups"]
        cs.history        = sess_state.get("history", [])
        cs.last_question  = sess_state.get("last_question")
        # apply the user's latest message
        cs.update_answers(user_msg, advisor.extract_fields)
        missing = cs.missing_fields()
        if not missing:
            assistant_msg = None
            done = True
        else:
            assistant_msg = cs.llm_generate_question(missing[:1])
            if assistant_msg is None:
                # If we can't generate a question, mark as done and provide final message
                assistant_msg = "I understand you're unsure about some details. That's okay! We can proceed with what we know."
                done = True
            else:
                done = False

    # 2) Build next-response state
    response_state = {
        "answers":       cs.answers,
        "follow_ups":    cs.follow_ups,
        "history":       cs.history,
        "last_question": cs.last_question
    }

    return Response({
        "user_id":           user_id,
        "session":           response_state,
        "assistant_message": assistant_msg,
        "missing_fields":    [] if done else cs.missing_fields(),
        "done":              done,
    })
