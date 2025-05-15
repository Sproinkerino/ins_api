from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

class ChatEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.chat_url = '/api/chat/'  # Use the full path instead of reverse
        print(f"Resolved chat_url: {self.chat_url}")  # Debug print
        self.test_user_id = "test_user_123"
        self.valid_payload = {
            "user_id": self.test_user_id,
            "session": None,
            "message": None
        }

    def test_missing_user_id(self):
        """Test that the endpoint returns 400 when user_id is missing"""
        payload = self.valid_payload.copy()
        payload.pop('user_id')
        
        response = self.client.post(self.chat_url, payload, format='json', follow=True)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_new_chat_session(self):
        """Test starting a new chat session"""
        response = self.client.post(self.chat_url, self.valid_payload, format='json', follow=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.test_user_id)
        self.assertIsNotNone(response.data['assistant_message'])
        self.assertFalse(response.data['done'])
        self.assertIn('session', response.data)
        
        # Store session state for next test
        return response.data['session']

    def test_continuing_chat_session(self):
        """Test continuing an existing chat session"""
        # First get initial session
        initial_session = self.test_new_chat_session()
        
        # Continue chat with a response
        payload = {
            "user_id": self.test_user_id,
            "session": initial_session,
            "message": "I am 30 years old"
        }
        
        response = self.client.post(self.chat_url, payload, format='json', follow=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.test_user_id)
        self.assertIsNotNone(response.data['session'])
        self.assertIn('answers', response.data['session'])
        
        # Verify the answer was captured
        self.assertIn('age', response.data['session']['answers'])
        self.assertEqual(response.data['session']['answers']['age'], '30')

    def test_complete_chat_flow(self):
        """Test a complete chat flow with all required fields"""
        session = None
        test_responses = [
            "I am 30 years old",
            "I have paid $50,000 so far",
            "I pay $500 monthly",
            "I have 20 years remaining",
            "My plan is called Premium Growth ILP"
        ]
        
        for response in test_responses:
            payload = {
                "user_id": self.test_user_id,
                "session": session,
                "message": response
            }
            
            api_response = self.client.post(self.chat_url, payload, format='json', follow=True)
            self.assertEqual(api_response.status_code, status.HTTP_200_OK)
            session = api_response.data['session']
            
            # On last response, verify we're done
            if response == test_responses[-1]:
                self.assertTrue(api_response.data['done'])
                self.assertEqual(len(api_response.data['missing_fields']), 0)
