"""Tests for the two-way Telegram ↔ SMS booking bridge."""

from __future__ import annotations

from app.adapters.mock import MockAdapter
from app.adapters.telegram_mock import MockTelegramAdapter
from app.bridge.hub import BridgeHub


def _hub():
    sms = MockAdapter()
    tg = MockTelegramAdapter()
    return BridgeHub(sms, tg), sms, tg


def test_start_inquiry_greets_tourist():
    hub, sms, tg = _hub()
    thread = hub.start_inquiry("chat1", "+251911000000", "amh", "Tomoca Coffee")
    assert thread.ref
    assert tg.outbox[-1].chat_id == "chat1"
    assert "Tomoca Coffee" in tg.outbox[-1].text


def test_tourist_message_relayed_to_owner_sms():
    hub, sms, tg = _hub()
    thread = hub.start_inquiry("chat1", "+251911000000", "amh", "Tomoca Coffee")
    tg.receive("chat1", "Do you have a table for two?")
    # an SMS went to the owner, tagged with the thread ref
    assert sms.outbox[-1].recipient == "+251911000000"
    assert f"[{thread.ref}]" in sms.outbox[-1].text
    assert "Tomoca Coffee" in sms.outbox[-1].text


def test_owner_reply_with_ref_routed_to_tourist():
    hub, sms, tg = _hub()
    thread = hub.start_inquiry("chat1", "+251911000000", "amh", "Tomoca Coffee")
    tg.receive("chat1", "Do you have a table?")
    before = len(tg.outbox)
    sms.receive("+251911000000", f"[{thread.ref}] yes we do")
    assert len(tg.outbox) > before
    assert tg.outbox[-1].chat_id == "chat1"
    assert "Tomoca Coffee replied" in tg.outbox[-1].text


def test_owner_reply_without_ref_routes_by_phone():
    hub, sms, tg = _hub()
    hub.start_inquiry("chat1", "+251911000000", "amh", "Tomoca Coffee")
    tg.receive("chat1", "hello")
    before = len(tg.outbox)
    sms.receive("+251911000000", "call me please")  # no ref
    assert len(tg.outbox) > before
    assert tg.outbox[-1].chat_id == "chat1"


def test_unknown_owner_sms_is_ignored():
    hub, sms, tg = _hub()
    hub.start_inquiry("chat1", "+251911000000", "amh", "Tomoca Coffee")
    before = len(tg.outbox)
    # an SMS from a number with no thread (e.g. an onboarding message)
    out = hub._on_owner_sms_text("+251999999999", "random")
    assert out == []
    assert len(tg.outbox) == before


def test_tourist_without_thread_is_prompted():
    hub, sms, tg = _hub()
    replies = tg.receive("stranger", "hi")
    assert "Message on Telegram" in replies[-1].text


def test_two_businesses_separate_threads():
    hub, sms, tg = _hub()
    t1 = hub.start_inquiry("chatA", "+251911111111", "amh", "Cafe A")
    t2 = hub.start_inquiry("chatB", "+251922222222", "orm", "Shop B")
    assert t1.ref != t2.ref
    tg.receive("chatA", "question A")
    tg.receive("chatB", "question B")
    # each owner got only their own tourist's message
    a_msgs = [m for m in sms.outbox if m.recipient == "+251911111111"]
    b_msgs = [m for m in sms.outbox if m.recipient == "+251922222222"]
    assert any("question A" in m.text for m in a_msgs)
    assert any("question B" in m.text for m in b_msgs)
    assert not any("question B" in m.text for m in a_msgs)
