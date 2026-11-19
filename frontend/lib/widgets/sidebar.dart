import 'package:flutter/material.dart';
import '../app_theme.dart';

class SidebarItem {
  final IconData icon;
  final String label;
  const SidebarItem({required this.icon, required this.label});
}

const sidebarItems = [
  SidebarItem(icon: Icons.chat_bubble_outline_rounded, label: 'Chat'),
  SidebarItem(icon: Icons.history_rounded, label: 'Sessions'),
  SidebarItem(icon: Icons.receipt_long_rounded, label: 'Activity'),
  SidebarItem(icon: Icons.check_circle_outline_rounded, label: 'Approvals'),
];

class Sidebar extends StatelessWidget {
  final int selectedIndex;
  final void Function(int) onSelect;
  final VoidCallback onLogout;

  const Sidebar({
    super.key,
    required this.selectedIndex,
    required this.onSelect,
    required this.onLogout,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 200,
      color: AppColors.surface,
      child: Column(
        children: [
          // Header
          Container(
            padding: const EdgeInsets.fromLTRB(16, 20, 16, 16),
            decoration: const BoxDecoration(
              border: Border(
                  bottom: BorderSide(color: AppColors.border)),
            ),
            child: Row(
              children: [
                Container(
                  width: 28,
                  height: 28,
                  decoration: BoxDecoration(
                    color: AppColors.accent.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(
                        color: AppColors.accent.withOpacity(0.3)),
                  ),
                  child: const Icon(Icons.memory_rounded,
                      color: AppColors.accent, size: 16),
                ),
                const SizedBox(width: 10),
                const Text(
                  'My Agent',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 8),

          // Nav items
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              itemCount: sidebarItems.length,
              itemBuilder: (context, index) {
                final item = sidebarItems[index];
                final isSelected = index == selectedIndex;

                return Container(
                  margin: const EdgeInsets.only(bottom: 2),
                  child: Material(
                    color: Colors.transparent,
                    borderRadius: BorderRadius.circular(6),
                    child: InkWell(
                      borderRadius: BorderRadius.circular(6),
                      onTap: () => onSelect(index),
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 9),
                        decoration: BoxDecoration(
                          color: isSelected
                              ? AppColors.accent.withOpacity(0.12)
                              : Colors.transparent,
                          borderRadius: BorderRadius.circular(6),
                          border: isSelected
                              ? Border.all(
                                  color: AppColors.accent.withOpacity(0.2))
                              : null,
                        ),
                        child: Row(
                          children: [
                            Icon(
                              item.icon,
                              size: 17,
                              color: isSelected
                                  ? AppColors.accent
                                  : AppColors.textSecondary,
                            ),
                            const SizedBox(width: 10),
                            Text(
                              item.label,
                              style: TextStyle(
                                color: isSelected
                                    ? AppColors.accent
                                    : AppColors.textSecondary,
                                fontSize: 13,
                                fontWeight: isSelected
                                    ? FontWeight.w600
                                    : FontWeight.normal,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),

          // Logout
          Container(
            decoration: const BoxDecoration(
              border: Border(top: BorderSide(color: AppColors.border)),
            ),
            padding: const EdgeInsets.all(8),
            child: Material(
              color: Colors.transparent,
              borderRadius: BorderRadius.circular(6),
              child: InkWell(
                borderRadius: BorderRadius.circular(6),
                onTap: onLogout,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 12, vertical: 9),
                  child: const Row(
                    children: [
                      Icon(Icons.logout_rounded,
                          size: 17, color: AppColors.textMuted),
                      SizedBox(width: 10),
                      Text(
                        'Disconnect',
                        style: TextStyle(
                            color: AppColors.textMuted, fontSize: 13),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}