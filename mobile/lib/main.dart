import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'screens/dashboard_screen.dart';
import 'services/api_service.dart';

void main() {
  runApp(
    ChangeNotifierProvider(
      create: (_) => LuminaProvider(),
      child: const LuminaApp(),
    ),
  );
}

class LuminaApp extends StatelessWidget {
  const LuminaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Lumina AI OS',
      theme: ThemeData.dark().copyWith(
        colorScheme: ColorScheme.dark(
          primary: Colors.cyan,
          secondary: Colors.cyanAccent,
        ),
        scaffoldBackgroundColor: const Color(0xFF030712),
      ),
      home: const DashboardScreen(),
    );
  }
}

class LuminaProvider extends ChangeNotifier {
  final ApiService api = ApiService();
  bool connected = false;
  String status = 'initializing';

  Future<void> connect() async {
    connected = await api.healthCheck();
    status = connected ? 'online' : 'offline';
    notifyListeners();
  }
}
