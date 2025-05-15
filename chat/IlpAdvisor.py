import os
import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from openai import OpenAI

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# from langchain_community.vectorstores import Chroma
# from langchain.chains import RetrievalQA
QUESTION_MAP = {
    'age': {
        'first': 'Hello! To start, may I know your age?',
        'followup': 'Great, thanks! Could you confirm your age once more for accuracy?'
    },
    'amount_paid': {
        'first': 'How much have you paid into your ILP so far?',
        'followup': 'Thanks! Just to confirm, what is the total amount you\'ve contributed to date?'
    },
    'payment_amount': {
        'first': 'What amount do you pay for your policy each period?',
        'followup': 'Understood. Can you specify the exact payment amount per {payment_frequency}?'
    },
    'payment_frequency': {
        'first': 'Do you make payments monthly or yearly for this policy?',
        'followup': 'Got it. Just to confirm, your payment frequency is {payment_frequency}, correct?'
    },
    'remaining_duration': {
        'first': 'How much longer (in years or months) do you have to pay?',
        'followup': 'Thanks! Can you confirm the remaining duration of your payments?'
    },
    'plan_name': {
        'first': 'Which ILP plan did you choose?',
        'followup': 'Great. Just to be precise, what is the exact name of your ILP plan?'
    }
}
FIELD_DESCRIPTIONS = {
    "age": "your current age in years",
    "amount_paid": "the total sum you have paid into your ILP so far",
    "payment_amount": "the amount you pay each period",
    "payment_frequency": "how often you make those payments (e.g., monthly or yearly)",
    "remaining_duration": "the remaining time (in years or months) you have left to pay",
    "plan_name": "the exact name of your current ILP plan"
}

class ChatSession:
    """
    Maintains session state for KYC collection, with one follow-up per field,
    and passes the assistant prompt to the extractor for full context.
    """
    def __init__(self, required_fields, llm):
        self.required_fields = required_fields
        self.answers = {field: None for field in required_fields}
        self.history = []
        self.follow_ups = {field: 0 for field in required_fields}
        self.llm = llm
        self.last_question = None

    def start_chat(self) -> str:
        # Phase 2: Kick-off with full-detail welcome prompt
        welcome = (
            "To help me provide the best advice, could you please share the following details?\n\n"
            "1. Your age\n"
            "2. The total amount you've paid so far\n"
            "3. What is your regular payment for this insurance plan and how often are you required to pay?\n"
            "4. The remaining duration of your plan\n"
            "5. The name of your current plan\n\n"
            "I appreciate your time—let's get started!"
        )

        self.last_question = welcome
        return welcome

    def update_answers(self, raw_message: str, extractor) -> None:
        """
        Phase 4.1: Parse message using both last assistant question and raw user reply.
        """
        parsed = extractor(self.last_question, raw_message)
        self.history.append({'assistant': self.last_question, 'user': raw_message, 'parsed': parsed})
        for field in self.required_fields:
            if parsed.get(field) and parsed[field].strip().lower() != 'unsure':
                self.answers[field] = parsed[field].strip()

    def missing_fields(self) -> list:
        """
        Phase 4.2: List fields still None or 'unsure'.
        """
        print(self.answers)
        return [f for f, v in self.answers.items() if not v]

    def llm_generate_question(self, fields: list) -> str:
        """
        Phase 4.4: Ask LLM to phrase a question for one missing field,
        include description and why it matters; store for extraction.
        """
        field = fields[0]
        # If already asked once, mark as unsure and skip
        if self.follow_ups[field] >= 1:
            self.answers[field] = 'unsure'
            self.last_question = None
            return None
        self.follow_ups[field] += 1
        description = FIELD_DESCRIPTIONS.get(field, field)
        prompt = (
            f"You are a knowledgeable financial advisor. You're collecting KYC data and need to request {description}. "
            f"Please include why this information helps personalize advice. "
            f"For example: 'To tailor my recommendation, could you share {description}?' "
            f"If the user doesn't know, they can reply with 'unsure'."
        )
        self.last_question = prompt
        return self.llm.predict(prompt)

    def print_summary(self) -> None:
        """
        Phase 5: Pretty-print collected answers.
        """
        print("\nAll KYC fields collected:")
        for f, v in self.answers.items():
            print(f"- {f}: {v}")

class ILPAdvisor:
    REQUIRED_FIELDS = list(QUESTION_MAP.keys())

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
        # emb = OpenAIEmbeddings()
        # vectordb = Chroma(
        #     persist_directory="./chromadb_dir",
        #     collection_name="prudential_ilp",
        #     embedding_function=emb
        # )
        # retriever = vectordb.as_retriever(search_kwargs={"k":4})
        # self.qa_chain = RetrievalQA.from_chain_type(
        #     llm=self.llm, chain_type="stuff", retriever=retriever, return_source_documents=False
        # )

    def extract_fields(self, question: str, message: str) -> dict:
        """
        Use GPT function-calling with full context (system, assistant question, user reply)
        to extract KYC fields from raw user message.
        """
        function_def = [{
            "name": "extract_user_data",
            "description": "Extract KYC fields: age, amount_paid, payment_amount, payment_frequency, remaining_duration, plan_name." + "You are a financial assistant tasked with extracting user KYC data. If the user sounds unsure about that question, mark the field as 'unsure'"
                        ,
            "parameters": {
                "type": "object",
                "properties": {
                    field: {"type": "string", "description": FIELD_DESCRIPTIONS[field]}
                    for field in self.REQUIRED_FIELDS
                },
                "required": []
            }
        }]
        messages = [
            {"role": "system", "content": "You are a financial assistant tasked with extracting user KYC data. If the user sounds unsure about that question, mark the field as 'unsure'"},
            {"role": "assistant", "content": f"Attached is the question given to the user :::\n{question if question else 'No specific question was asked'}"},
            {"role": "user", "content": message}
        ]
        resp = self.client.chat.completions.create(
            model=self.llm.model_name,
            messages=messages,
            functions=function_def,
            function_call={"name": "extract_user_data"}
        )
        msg = resp.choices[0].message
        if getattr(msg, 'function_call', None):
            return json.loads(msg.function_call.arguments)
        try:
            return json.loads(msg.content)
        except json.JSONDecodeError:
            return {}

    def analyze_policy(self, user_data: dict) -> list:
        plan = user_data['plan_name']
        policy_info = self.qa_chain.run(plan)
        prompt = (
            f"User profile:\n"
            f"- Age: {user_data['age']}\n"
            f"- Paid so far: {user_data['amount_paid']}\n"
            f"- {user_data['payment_frequency'].capitalize()} payment: {user_data['payment_amount']}\n"
            f"- Remaining duration: {user_data['remaining_duration']}\n\n"
            f"Policy details:\n{policy_info}\n\n"
            "1) Explain why this ILP may be suboptimal.\n"
            "2) Compute hypothetical returns for VWRA, SPY, STI.\n"
            "Provide JSON array with {date,instrument,value}."
        )
        resp = self.client.chat.completions.create(
            model=self.llm.model_name,
            messages=[{"role":"user","content":prompt}]
        )
        return json.loads(resp.choices[0].message.content)

    def plot_returns(self, records: list) -> None:
        df = pd.DataFrame(records)
        sns.lineplot(data=df, x="date", y="value", hue="instrument")
        plt.title("ILP vs VWRA vs SPY vs STI")
        plt.tight_layout()
        plt.savefig("comparison.png")

if __name__ == '__main__':
    advisor = ILPAdvisor()
    session = ChatSession(ILPAdvisor.REQUIRED_FIELDS, advisor.llm)
    # Phase 2: Kick-off
    print("Advisor:", session.start_chat())
    # Iterative fill-loop
    while session.missing_fields():
        msg = input("User: ")
        session.update_answers(msg, advisor.extract_fields)
        missing = session.missing_fields()
        if not missing:
            break
        question = session.llm_generate_question(missing[:1])
        if question:
            print("Advisor:", question)
    # Completion
    session.print_summary()
