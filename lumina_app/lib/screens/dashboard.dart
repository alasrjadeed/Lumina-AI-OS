import 'package:flutter/material.dart';
import '../services/api_service.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final api = ApiService();
  Map<String, dynamic>? health;
  List<String> endpoints = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final root = await api.get('/');
      final h = await api.get('/system/health');
      setState(() {
        health = h;
        endpoints = (root['endpoints'] as Map<String, dynamic>).keys.toList();
      });
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Lumina AI OS')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Icon(Icons.circle, color: health?['status'] == 'ok' ? Colors.green : Colors.red, size: 12),
                    const SizedBox(width: 8),
                    Text('Status: ${health?['status'] ?? '...'}'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text('Endpoints', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            ...endpoints.map((e) => ListTile(
              leading: const Icon(Icons.link, size: 16),
              title: Text(e),
              dense: true,
            )),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ChatScreen())),
        child: const Icon(Icons.chat),
      ),
    );
  }
}
