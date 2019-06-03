import codecs

from xelor.message import ChatMessage


def test_chat_message():
    data = b"02000573656b73655cb6326d00086e6d71677477376b422f5bd801bc0000000647796174736f00000520a46b"
    data = codecs.decode(data, "hex")
    chat_message = ChatMessage(data)
    assert chat_message.message == "sekse"
    assert chat_message.canal == 2
    assert chat_message.name == "Gyatso"
    assert chat_message.timestamp == 1555444333
