import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_theme.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';
import '../widgets/sidebar.dart';
import 'chat_screen.dart';
import 'sessions_screen.dart';
import 'activity_screen.dart';
import 'approvals_screen.dart';

class HomeScreen extends StatefulWidget {
  final ApiService apiService;
  const HomeScreen({super.key, required this.apiService});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;
  String _currentSessionId = 'default';

  void _onSessionSelected(String sessionId) {
    setState(() {
      _currentSessionId = sessionId;
      _selectedIndex = 0; // switch to chat
    });
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      ChatScreen(
        apiService: widget.apiService,
        sessionId: _currentSessionId,
        onSessionChange: (id) => setState(() => _currentSessionId = id),
      ),
      SessionsScreen(
        apiService: widget.apiService,
        onSessionSelected: _onSessionSelected,
      ),
      ActivityScreen(apiService: widget.apiService),
      ApprovalsScreen(
        apiService: widget.apiService,
        sessionId: _currentSessionId,
      ),
    ];

    return Scaffold(
      backgroundColor: AppColors.background,
      body: Row(
        children: [
          // Sidebar
          Sidebar(
            selectedIndex: _selectedIndex,
            onSelect: (index) => setState(() => _selectedIndex = index),
            onLogout: () async {
              await context.read<AuthProvider>().logout();
            },
          ),

          // Vertical divider
          Container(width: 1, color: AppColors.border),

          // Main content
          Expanded(child: screens[_selectedIndex]),
        ],
      ),
    );
  }
}