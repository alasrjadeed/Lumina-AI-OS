import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final api = ApiService();
  final controller = TextEditingController();
  final messages = <Map<String, String>>[];
  bool loading = false;

  Future<void> send() async {
    final text = controller.text.trim();
    if (text.isEmpty) return;
    controller.clear();
    setState(() {
      messages.add({'role': 'user', 'content': text});
      loading = true;
    });
    try {
      final reply = await api.chat(text);
      setState(() {
        messages.add({'role': 'assistant', 'content': reply});
        loading = false;
      });
    } catch (e) {
      setState(() => loading = false);
    }
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Chat')),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: messages.length + (loading ? 1 : 0),
              itemBuilder: (ctx, i) {
                if (i == messages.length) {
                  return const Card(child: Padding(padding: EdgeInsets.all(12), child: Text('Thinking...')));
                }
                final msg = messages[i];
                final isUser = msg['role'] == 'user';
                return Align(
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Card(
                    color: isUser ? Colors.indigo.shade800 : Colors.grey.shade900,
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Text(msg['content'] ?? '', style: const TextStyle(fontSize: 14)),
                    ),
                  ),
                );
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: controller,
                    decoration: const InputDecoration(hintText: 'Type a message...'),
                    onSubmitted: (_) => send(),
                  ),
                ),
                IconButton(onPressed: send, icon: const Icon(Icons.send)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
