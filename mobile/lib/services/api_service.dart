import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  final String baseUrl = 'http://localhost:8000/api';

  Future<bool> healthCheck() async {
    try {
      final res = await http.get(Uri.parse('http://localhost:8000/health'));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<Map<String, dynamic>> login(String username, String password) async {
    final res = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'password': password}),
    );
    return jsonDecode(res.body);
  }

  Future<Map<String, dynamic>> getDashboard() async {
    final res = await http.get(Uri.parse('$baseUrl/dashboard/'));
    return jsonDecode(res.body);
  }

  Future<Map<String, dynamic>> explain(String topic, String level) async {
    final res = await http.post(
      Uri.parse('$baseUrl/explain/text'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'topic': topic, 'level': level}),
    );
    return jsonDecode(res.body);
  }
}
