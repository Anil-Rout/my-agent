import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config.dart';

class ApiService {
  final String baseUrl;
  String? token;

  ApiService({
    String? baseUrl,
    String? initialToken,
  })  : baseUrl = baseUrl ?? ServerConfig.baseUrl,
        token = initialToken;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };

  // ─── Auth ────────────────────────────────────────────────────

  Future<String> login(String password) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/auth/login'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'password': password}),
        )
        .timeout(const Duration(seconds: 10));

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      token = data['access_token'] as String;
      return token!;
    }

    final error = jsonDecode(response.body);
    throw Exception(error['detail'] ?? 'Login failed');
  }

  void logout() => token = null;

  // ─── Chat ────────────────────────────────────────────────────

  Future<Map<String, dynamic>> sendMessage(
    String message, {
    String sessionId = 'default',
    List<Map<String, String>> history = const [],
  }) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/chat/'),
          headers: _headers,
          body: jsonEncode({
            'message': message,
            'session_id': sessionId,
            'history': history,
          }),
        )
        .timeout(const Duration(seconds: 60));

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    final error = jsonDecode(response.body);
    throw Exception(error['detail'] ?? 'Chat failed');
  }

  Future<List<dynamic>> getHistory(String sessionId, {int limit = 50}) async {
    final response = await http
        .get(
          Uri.parse('$baseUrl/chat/history?session_id=$sessionId&limit=$limit'),
          headers: _headers,
        )
        .timeout(const Duration(seconds: 10));

    if (response.statusCode == 200) {
      return (jsonDecode(response.body)['history'] as List?) ?? [];
    }
    throw Exception('Failed to load history');
  }

  Future<List<dynamic>> getSessions({int limit = 30}) async {
    final response = await http
        .get(
          Uri.parse('$baseUrl/chat/sessions?limit=$limit'),
          headers: _headers,
        )
        .timeout(const Duration(seconds: 10));

    if (response.statusCode == 200) {
      return (jsonDecode(response.body)['sessions'] as List?) ?? [];
    }
    throw Exception('Failed to load sessions');
  }

  Future<List<dynamic>> getTasks({String? sessionId, int limit = 30}) async {
    final query = sessionId != null
        ? '?session_id=$sessionId&limit=$limit'
        : '?limit=$limit';
    final response = await http
        .get(
          Uri.parse('$baseUrl/chat/tasks$query'),
          headers: _headers,
        )
        .timeout(const Duration(seconds: 10));

    if (response.statusCode == 200) {
      return (jsonDecode(response.body)['tasks'] as List?) ?? [];
    }
    throw Exception('Failed to load tasks');
  }

  // ─── System ──────────────────────────────────────────────────

  Future<List<dynamic>> getActivity({int limit = 30}) async {
    final response = await http
        .get(
          Uri.parse('$baseUrl/system/activity?limit=$limit'),
          headers: _headers,
        )
        .timeout(const Duration(seconds: 10));

    if (response.statusCode == 200) {
      return (jsonDecode(response.body)['activity'] as List?) ?? [];
    }
    throw Exception('Failed to load activity');
  }

  Future<Map<String, dynamic>> getActivitySummary() async {
    final response = await http
        .get(Uri.parse('$baseUrl/system/summary'), headers: _headers)
        .timeout(const Duration(seconds: 10));

    if (response.statusCode == 200) {
      return (jsonDecode(response.body)['summary'] as Map<String, dynamic>?) ?? {};
    }
    throw Exception('Failed to load summary');
  }

  // ─── Approvals ───────────────────────────────────────────────

  Future<List<dynamic>> getApprovals(String sessionId) async {
    final response = await http
        .get(
          Uri.parse('$baseUrl/tools/approvals/$sessionId'),
          headers: _headers,
        )
        .timeout(const Duration(seconds: 10));

    if (response.statusCode == 200) {
      return (jsonDecode(response.body)['approvals'] as List?) ?? [];
    }
    throw Exception('Failed to load approvals');
  }

  Future<void> approveAction(int approvalId) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/tools/approvals/$approvalId/approve'),
          headers: _headers,
        )
        .timeout(const Duration(seconds: 10));

    if (response.statusCode != 200) {
      throw Exception('Failed to approve action');
    }
  }

  Future<void> denyAction(int approvalId) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/tools/approvals/$approvalId/deny'),
          headers: _headers,
        )
        .timeout(const Duration(seconds: 10));

    if (response.statusCode != 200) {
      throw Exception('Failed to deny action');
    }
  }

  // ─── Tools ───────────────────────────────────────────────────

  Future<List<dynamic>> getTools() async {
    final response = await http
        .get(Uri.parse('$baseUrl/tools/list'), headers: _headers)
        .timeout(const Duration(seconds: 10));

    if (response.statusCode == 200) {
      return (jsonDecode(response.body) as List?) ?? [];
    }
    throw Exception('Failed to load tools');
  }
}