"""
WebSocket consumers for WebRTC signaling and real-time communication.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()

# In-memory buffering for consultation WebRTC calls.
# This is mainly to support "incoming call" behavior across pages:
# if the receiver opens the consultation room after the offer was sent,
# we can replay the latest offer + ICE candidates.
CONSULTATION_PENDING_CALLS = {}


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat messaging.
    Handles sending and receiving messages without page refresh.
    """
    
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
            
        # Verify user is part of this conversation
        if not await self.user_can_access_conversation():
            await self.close()
            return
        
        # Join conversation group
        await self.channel_layer.group_add(
            self.conversation_group_name,
            self.channel_name
        )
        
        # Also join user's personal notification group
        self.user_group_name = f'user_{self.user.id}'
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave conversation group
        if hasattr(self, 'conversation_group_name'):
            await self.channel_layer.group_discard(
                self.conversation_group_name,
                self.channel_name
            )
        
        # Leave user notification group
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming messages from WebSocket."""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'send_message':
            content = data.get('content', '').strip()
            if content:
                # Save message to database
                message = await self.save_message(content)
                
                # Broadcast message to conversation group
                await self.channel_layer.group_send(
                    self.conversation_group_name,
                    {
                        'type': 'chat_message',
                        'message': {
                            'id': message.id,
                            'content': message.content,
                            'sender': message.sender.username,
                            'sender_name': message.sender.get_full_name() or message.sender.username,
                            'sender_profile_picture': await self.get_sender_avatar(message.sender),
                            'created_at': message.created_at.strftime('%H:%M'),
                            'message_type': message.message_type,
                            'prescription_id': message.prescription.id if message.prescription else None,
                        }
                    }
                )
    
    async def chat_message(self, event):
        """Send message to WebSocket."""
        # Support both nested 'message' object and flat fields for backward compatibility
        if 'message' in event:
            message_data = event['message']
        else:
            message_data = {
                'id': event.get('message_id'),
                'content': event.get('content'),
                'sender': event.get('sender_username'),
                'sender_name': event.get('sender_username'),
                'sender_profile_picture': event.get('sender_avatar'),
                'created_at': event.get('timestamp'),
                'message_type': event.get('message_type'),
                'prescription_id': event.get('prescription_id'),
            }
            
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message_data
        }))
    
    @database_sync_to_async
    def save_message(self, content):
        """Save message to database."""
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content
        )
        return message
    
    @database_sync_to_async
    def user_can_access_conversation(self):
        """Check if user has permission to access conversation."""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return self.user in [conversation.patient, conversation.provider]
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_sender_avatar(self, user):
        """Get sender's avatar URL or initials."""
        if user.profile_picture:
            return user.profile_picture.url
        else:
            return None


class CallConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for WebRTC video/audio call signaling.
    Handles offer, answer, and ICE candidate exchange between peers.
    Also handles real-time call notifications.
    """
    
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'call_{self.room_name}'
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Also join user's personal notification group
        self.user_group_name = f'user_{self.user.id}'
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notify others that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': str(self.user.id),
                'username': self.user.username,
                'message': f'{self.user.username} joined the call'
            }
        )
    
    async def disconnect(self, close_code):
        # Leave room group (if exists)
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        # Leave user notification group (if exists)
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        
        # Notify others that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': str(self.user.id),
                'username': self.user.username,
                'message': f'{self.user.username} left the call'
            }
        )
    
    async def receive(self, text_data):
        """Handle incoming WebRTC signaling messages."""
        print(f'CallConsumer received message from user {self.user.username}: {text_data}')
        data = json.loads(text_data)
        message_type = data.get('type')
        print(f'Message type: {message_type}')
        
        if message_type == 'offer':
            print(f'Forwarding offer from {self.user.username} to room {self.room_group_name}')
            # Forward offer to other peer
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_offer',
                    'offer': data['offer'],
                    'sender_id': str(self.user.id),
                    'sender_name': self.user.username
                }
            )
            print('Offer forwarded successfully')
        
        elif message_type == 'answer':
            print(f'Forwarding answer from {self.user.username} to room {self.room_group_name}')
            # Forward answer to other peer
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_answer',
                    'answer': data['answer'],
                    'sender_id': str(self.user.id),
                    'sender_name': self.user.username
                }
            )
            print('Answer forwarded successfully')
        
        elif message_type == 'ice_candidate':
            print(f'Forwarding ICE candidate from {self.user.username} to room {self.room_group_name}')
            # Forward ICE candidate to other peer
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_ice_candidate',
                    'candidate': data['candidate'],
                    'sender_id': str(self.user.id),
                    'sender_name': self.user.username
                }
            )
            print('ICE candidate forwarded successfully')
        
        elif message_type == 'call_ended':
            # Notify call ended
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'call_ended',
                    'sender_id': str(self.user.id),
                    'sender_name': self.user.username
                }
            )
        
        elif message_type == 'call_rejected':
            # Notify call rejected
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'call_rejected',
                    'sender_id': str(self.user.id),
                    'sender_name': self.user.username
                }
            )
    
    # Handler methods for group messages
    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username'],
            'message': event['message']
        }))
    
    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username'],
            'message': event['message']
        }))
    
    async def webrtc_offer(self, event):
        print(f'Sending offer to user {self.user.username} from {event["sender_name"]}')
        # Don't send back to sender
        if str(self.user.id) != event['sender_id']:
            await self.send(text_data=json.dumps({
                'type': 'offer',
                'offer': event['offer'],
                'sender_id': event['sender_id'],
                'sender_name': event['sender_name']
            }))
            print(f'Offer sent successfully to {self.user.username}')
        else:
            print(f'Not sending offer back to sender {self.user.username}')
    
    async def webrtc_answer(self, event):
        print(f'Sending answer to user {self.user.username} from {event["sender_name"]}')
        # Don't send back to sender
        if str(self.user.id) != event['sender_id']:
            await self.send(text_data=json.dumps({
                'type': 'answer',
                'answer': event['answer'],
                'sender_id': event['sender_id'],
                'sender_name': event['sender_name']
            }))
            print(f'Answer sent successfully to {self.user.username}')
        else:
            print(f'Not sending answer back to sender {self.user.username}')
    
    async def webrtc_ice_candidate(self, event):
        # Don't send back to sender
        if str(self.user.id) != event['sender_id']:
            await self.send(text_data=json.dumps({
                'type': 'ice_candidate',
                'candidate': event['candidate'],
                'sender_id': event['sender_id'],
                'sender_name': event['sender_name']
            }))
    
    async def call_ended(self, event):
        print(f'Call ended event received by user {self.user.username}: {event}')
        await self.send(text_data=json.dumps({
            'type': 'call_ended',
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'message': event.get('message', 'Call ended')
        }))
    
    async def call_rejected(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_rejected',
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name']
        }))
    
    # Handler for incoming call notifications
    async def incoming_call(self, event):
        """Send incoming call notification to user"""
        # Only send to the intended recipient
        if str(self.user.id) == str(event['recipient_id']):
            await self.send(text_data=json.dumps({
                'type': 'incoming_call',
                'caller_id': event['caller_id'],
                'caller_name': event['caller_name'],
                'call_type': event['call_type'],
                'room_id': event['room_id'],
                'call_id': event['call_id'],
                'redirect_url': event.get('redirect_url'),
            }))
    
    # Handler for call status updates
    async def call_status_update(self, event):
        """Send call status updates"""
        await self.send(text_data=json.dumps({
            'type': 'call_status_update',
            'call_id': event['call_id'],
            'status': event['status'],
            'message': event['message']
        }))
    
    # Handler for call notifications
    async def call_notification(self, event):
        """Send call notification to user"""
        await self.send(text_data=json.dumps({
            'type': 'incoming_call',  # Changed from 'call_notification' to match base.html
            'call_id': event['call_id'],
            'caller_id': event['caller_id'],
            'caller_name': event['caller_name'],
            'call_type': event['call_type'],
            'room_id': event['room_id'],
            'timestamp': event['timestamp']
        }))


class ConsultationCallConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for WebRTC video/audio call signaling in consultation rooms.
    Handles offer, answer, and ICE candidate exchange between peers.
    """
    
    async def connect(self):
        self.consultation_id = self.scope['url_route']['kwargs']['consultation_id']
        self.room_group_name = f'consultation_call_{self.consultation_id}'
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

        # If there's a pending consultation call offer, replay it to the user.
        # This allows receivers to accept from other parts of the app.
        pending_key = str(self.consultation_id)
        pending = CONSULTATION_PENDING_CALLS.pop(pending_key, None)
        if pending:
            try:
                await self.send(text_data=json.dumps({
                    'type': 'offer',
                    'from': pending['sender_name'],
                    'from_username': pending['from_username'],
                    'offer': pending['offer'],
                    'callId': pending['callId'],
                    'isVideo': pending['isVideo'],
                }))
                for candidate in pending.get('ice_candidates', []):
                    await self.send(text_data=json.dumps({
                        'type': 'ice_candidate',
                        'sender_name': pending['sender_name'],
                        'candidate': candidate,
                    }))
            except Exception:
                # Never block connection because of call replay
                pass
        
        # Notify others that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': str(self.user.id),
                'username': self.user.username,
                'message': f'{self.user.username} joined the consultation call'
            }
        )
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Notify others that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': str(self.user.id),
                'username': self.user.username,
                'message': f'{self.user.username} left the consultation call'
            }
        )
    
    async def receive(self, text_data):
        """Handle incoming WebRTC signaling messages."""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'offer':
            # Buffer latest offer (and subsequent ICE candidates) so the receiver
            # can join later from other pages and still get the call.
            try:
                CONSULTATION_PENDING_CALLS[str(self.consultation_id)] = {
                    'sender_name': self.user.get_full_name() or self.user.username,
                    'from_username': self.user.username,
                    'offer': data.get('offer'),
                    'callId': data.get('callId', ''),
                    'isVideo': data.get('isVideo', True),
                    'ice_candidates': [],
                }
            except Exception:
                pass

            # Send a global "incoming_call" notification to the other participant
            # so the popup works across the entire app (not just inside the room).
            #
            # Note: Consultation calls don't use the messaging.Call model, so call_id may be missing.
            try:
                from consultations.models import Consultation

                consultation = await database_sync_to_async(
                    lambda: Consultation.objects.select_related(
                        "appointment__patient",
                        "appointment__provider",
                    ).get(pk=self.consultation_id)
                )()
                sender_id = str(self.user.id)
                # Determine the other participant in the consultation.
                # Use appointment.* fields to avoid triggering lazy DB queries via properties.
                receiver = (
                    consultation.appointment.provider
                    if str(consultation.appointment.patient_id) == sender_id
                    else consultation.appointment.patient
                )
                call_type = 'VIDEO' if data.get('isVideo', True) else 'AUDIO'
                # `consultations/urls.py` routes `room/<pk>/` to `consultation_room(request, pk)`
                # where `pk` is an Appointment id (not a Consultation id).
                redirect_url = f"/consultations/room/{consultation.appointment_id}/"
                call_id = data.get('callId', '')

                await self.channel_layer.group_send(
                    f'user_{receiver.id}',
                    {
                        'type': 'incoming_call',
                        'recipient_id': receiver.id,
                        'caller_id': self.user.id,
                        'caller_name': self.user.get_full_name() or self.user.username,
                        'call_type': call_type,
                        'room_id': str(self.consultation_id),
                        'call_id': call_id,
                        'redirect_url': redirect_url,
                    }
                )
            except Exception:
                # If notification fails, we still want the WebRTC signaling to work.
                pass

            # Forward offer to other peer
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_offer',
                    'offer': data['offer'],
                    'sender_id': str(self.user.id),
                    'sender_name': self.user.get_full_name() or self.user.username,
                    'from_username': self.user.username,
                    'callId': data.get('callId', ''),
                    'isVideo': data.get('isVideo', True)
                }
            )
        
        elif message_type == 'answer':
            # Forward answer to other peer
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_answer',
                    'answer': data['answer'],
                    'sender_id': str(self.user.id),
                    'sender_name': self.user.get_full_name() or self.user.username,
                    'from_username': self.user.username,
                    'callId': data.get('callId', '')
                }
            )
        
        elif message_type == 'ice_candidate':
            # Buffer ICE candidates if we have a pending offer for this consultation.
            try:
                pending = CONSULTATION_PENDING_CALLS.get(str(self.consultation_id))
                if pending and data.get('candidate'):
                    pending.setdefault('ice_candidates', []).append(data['candidate'])
            except Exception:
                pass

            # Forward ICE candidate to other peer
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_ice_candidate',
                    'candidate': data['candidate'],
                    'sender_id': str(self.user.id),
                    'sender_name': self.user.username,
                    'to': data.get('to', '')
                }
            )
        
        elif message_type == 'call_ended':
            # Clear buffered data for this consultation call.
            CONSULTATION_PENDING_CALLS.pop(str(self.consultation_id), None)
            # Notify call ended
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'call_ended',
                    'sender_id': str(self.user.id),
                    'sender_name': self.user.username
                }
            )
        
        elif message_type == 'call_declined':
            # Clear buffered data for this consultation call.
            CONSULTATION_PENDING_CALLS.pop(str(self.consultation_id), None)
            # Notify call declined
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'call_declined',
                    'sender_id': str(self.user.id),
                    'sender_name': self.user.username,
                    'to': data.get('to', ''),
                    'callId': data.get('callId', ''),
                    'from': data.get('from', '')
                }
            )
    
    # Handler methods for group messages
    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username'],
            'message': event['message']
        }))
    
    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username'],
            'message': event['message']
        }))
    
    async def webrtc_offer(self, event):
        # Don't send back to sender
        if str(self.user.id) != event['sender_id']:
            await self.send(text_data=json.dumps({
                'type': 'offer',
                'offer': event['offer'],
                'from': event['sender_name'],
                'from_username': event['from_username'],
                'callId': event['callId'],
                'isVideo': event['isVideo'],
                'sender_id': event['sender_id']
            }))

    async def webrtc_answer(self, event):
        # Don't send back to sender
        if str(self.user.id) != event['sender_id']:
            await self.send(text_data=json.dumps({
                'type': 'answer',
                'answer': event['answer'],
                'from': event['sender_name'],
                'from_username': event['from_username'],
                'sender_id': event['sender_id'],
                'sender_name': event['sender_name']
            }))
    
    async def webrtc_ice_candidate(self, event):
        # Don't send back to sender
        if str(self.user.id) != event['sender_id']:
            await self.send(text_data=json.dumps({
                'type': 'ice_candidate',
                'candidate': event['candidate'],
                'sender_id': event['sender_id'],
                'sender_name': event['sender_name']
            }))
    
    async def call_ended(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_ended',
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name']
        }))
    
    async def call_declined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_declined',
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'to': event['to'],
            'callId': event['callId'],
            'from': event['from']
        }))