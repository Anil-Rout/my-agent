import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../app_theme.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';
import 'chat_screen.dart';
import 'sessions_screen.dart';
import 'activity_screen.dart';
import 'approvals_screen.dart';

class MobileHomeScreen extends StatefulWidget {
  final ApiService apiService;
  const MobileHomeScreen({super.key, required this.apiService});

  @override
  State<MobileHomeScreen> createState() => _MobileHomeScreenState();
}

class _MobileHomeScreenState extends State<MobileHomeScreen> {
  int _selectedIndex = 0;
  String _currentSessionId = 'default';

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
        onSessionSelected: (id) => setState(() {
          _currentSessionId = id;
          _selectedIndex = 0;
        }),
      ),
      ActivityScreen(apiService: widget.apiService),
      ApprovalsScreen(
        apiService: widget.apiService,
        sessionId: _currentSessionId,
      ),
    ];

    return Scaffold(
      backgroundColor: AppColors.background,
      body: screens[_selectedIndex],
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          color: AppColors.surface,
          border: Border(top: BorderSide(color: AppColors.border)),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 6),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _NavItem(
                  icon: Icons.chat_bubble_outline_rounded,
                  label: 'Chat',
                  selected: _selectedIndex == 0,
                  onTap: () => setState(() => _selectedIndex = 0),
                ),
                _NavItem(
                  icon: Icons.history_rounded,
                  label: 'Sessions',
                  selected: _selectedIndex == 1,
                  onTap: () => setState(() => _selectedIndex = 1),
                ),
                _NavItem(
                  icon: Icons.receipt_long_rounded,
                  label: 'Activity',
                  selected: _selectedIndex == 2,
                  onTap: () => setState(() => _selectedIndex = 2),
                ),
                _NavItem(
                  icon: Icons.check_circle_outline_rounded,
                  label: 'Approvals',
                  selected: _selectedIndex == 3,
                  onTap: () => setState(() => _selectedIndex = 3),
                ),
                _NavItem(
                  icon: Icons.logout_rounded,
                  label: 'Logout',
                  selected: false,
                  onTap: () async {
                    await context.read<AuthProvider>().logout();
                  },
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _NavItem({
    required this.icon,
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: 22,
            color: selected ? AppColors.accent : AppColors.textMuted,
          ),
          const SizedBox(height: 3),
          Text(
            label,
            style: TextStyle(
              fontSize: 10,
              color: selected ? AppColors.accent : AppColors.textMuted,
              fontWeight:
                  selected ? FontWeight.w600 : FontWeight.normal,
            ),
          ),
        ],
      ),
    );
  }
}