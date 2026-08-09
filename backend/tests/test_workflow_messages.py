import unittest

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.graph.workflow import ChatWorkflow
from app.prompts.chat_prompt import SYSTEM_PROMPT


class WorkflowMessageTests(unittest.TestCase):
    def test_history_and_current_message_are_included(self):
        history = [
            {"role": "user", "content": "who is cm of ap?"},
            {"role": "assistant", "content": "The current Chief Minister is Y. S. Jagan Mohan Reddy."},
        ]

        messages = ChatWorkflow.build_messages(
            message="why",
            memory_context="User Personal Memory:\nName: Indira",
            history=history,
        )

        self.assertIsInstance(messages[0], SystemMessage)
        self.assertEqual(messages[0].content, SYSTEM_PROMPT)
        self.assertIsInstance(messages[1], SystemMessage)
        self.assertIn("User Personal Memory", messages[1].content)
        self.assertIsInstance(messages[2], HumanMessage)
        self.assertEqual(messages[2].content, "who is cm of ap?")
        self.assertIsInstance(messages[3], AIMessage)
        self.assertEqual(messages[3].content, "The current Chief Minister is Y. S. Jagan Mohan Reddy.")
        self.assertIsInstance(messages[4], HumanMessage)
        self.assertEqual(messages[4].content, "why")


if __name__ == "__main__":
    unittest.main()
