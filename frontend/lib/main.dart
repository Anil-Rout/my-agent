import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app_theme.dart';
import 'providers/auth_provider.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/mobile_home_screen.dart';
import 'services/api_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final prefs = await SharedPreferences.getInstance();
  final savedToken = prefs.getString('auth_token');

  final apiService = ApiService(initialToken: savedToken);

  runApp(
    ChangeNotifierProvider(
      create: (_) => AuthProvider(apiService: apiService, savedToken: savedToken),
      child: MyAgentApp(apiService: apiService),
    ),
  );
}

class MyAgentApp extends StatelessWidget {
  final ApiService apiService;
  const MyAgentApp({super.key, required this.apiService});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return MaterialApp(
      title: 'My Agent',
      debugShowCheckedModeBanner: false,
      theme: buildAppTheme(),
      home: auth.isLoggedIn
          ? (Platform.isAndroid || Platform.isIOS
              ? MobileHomeScreen(apiService: apiService)
              : HomeScreen(apiService: apiService))
          : LoginScreen(apiService: apiService),
    );
  }
}