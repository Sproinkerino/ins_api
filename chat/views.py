from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Create your views here.

def process_chat_message(message: str) -> str:
    """
    Dummy function to process chat messages.
    In a real application, this is where you'd put your chatbot logic.
    """
    return f"Received your message: {message}"

@api_view(['POST'])
def chat_endpoint(request):
    """
    API endpoint that accepts chat messages and returns responses.
    """
    try:
        message = request.data.get('message', '')
        if not message:
            return Response(
                {'error': 'Message is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process the message
        response = process_chat_message(message)
        
        return Response({'response': response})
    
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
