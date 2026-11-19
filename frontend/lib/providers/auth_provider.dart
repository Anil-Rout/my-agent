import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';

class AuthProvider extends ChangeNotifier {
  final ApiService apiService;
  bool _isLoggedIn;

  AuthProvider({required this.apiService, String? savedToken})
      : _isLoggedIn = savedToken != null;

  bool get isLoggedIn => _isLoggedIn;

  Future<void> login(String password) async {
    final token = await apiService.login(password);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('auth_token', token);
    _isLoggedIn = true;
    notifyListeners();
  }

  Future<void> logout() async {
    apiService.logout();
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    _isLoggedIn = false;
    notifyListeners();
  }
}