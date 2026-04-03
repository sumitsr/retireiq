import pytest
import json
import queue
from app.services.sse_service import SSEService

def test_sse_format():
    """Verify the SSE wire format is correct."""
    service = SSEService()
    formatted = service._format_sse("test_event", {"foo": "bar"})
    assert formatted == 'event: test_event\ndata: {"foo": "bar"}\n\n'

def test_sse_subscription_and_publish():
    """Verify that publishing an event to a session reaches the subscriber."""
    service = SSEService()
    session_id = "test-session"
    
    # Manually trigger the subscription generator to get the queue
    gen = service.subscribe(session_id)
    
    # First item from subscribe() is always the 'connected' event
    first_event = next(gen)
    assert 'event: connected' in first_event

    # Publish an event
    service.publish(session_id, "agent_thought", {"text": "I am thinking"})
    
    # Get the next item from the generator
    second_event = next(gen)
    assert 'event: agent_thought' in second_event
    assert '"text": "I am thinking"' in second_event

def test_sse_multiple_subscribers():
    """Verify that broadcasting to a session reaches all active listeners."""
    service = SSEService()
    session_id = "broadcast-session"
    
    gen1 = service.subscribe(session_id)
    gen2 = service.subscribe(session_id)
    
    # Clear the initial 'connected' event
    next(gen1)
    next(gen2)
    
    service.publish(session_id, "hello", {"msg": "world"})
    
    res1 = next(gen1)
    res2 = next(gen2)
    
    assert "world" in res1
    assert "world" in res2

def test_sse_cleanup_on_disconnect():
    """Verify that listeners are removed when the generator is closed."""
    service = SSEService()
    session_id = "cleanup-session"
    
    gen = service.subscribe(session_id)
    next(gen) # start it
    
    assert len(service.listeners[session_id]) == 1
    
    # Simulate client disconnect by closing the generator
    gen.close()
    
    # We need to trigger the GeneratorExit by trying to pull or just manually checking since we closed it
    # In the actual service, the 'while True' loop handles the GeneratorExit cleanup.
    # To test the lock/cleanup logic directly:
    with pytest.raises(StopIteration):
        next(gen)
        
    assert session_id not in service.listeners
