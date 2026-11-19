import 'package:flutter/material.dart';

class AppColors {
  // Base
  static const background = Color(0xFF0D1117);
  static const surface = Color(0xFF161B22);
  static const panel = Color(0xFF21262D);
  static const border = Color(0xFF30363D);

  // Text
  static const textPrimary = Color(0xFFE6EDF3);
  static const textSecondary = Color(0xFF8B949E);
  static const textMuted = Color(0xFF484F58);

  // Accent
  static const accent = Color(0xFF58A6FF);
  static const accentDim = Color(0xFF1F6FEB);

  // Status
  static const success = Color(0xFF3FB950);
  static const warning = Color(0xFFD29922);
  static const danger = Color(0xFFF85149);
  static const info = Color(0xFF79C0FF);

  // User message bubble
  static const userBubble = Color(0xFF1F6FEB);
  static const agentBubble = Color(0xFF21262D);
}

ThemeData buildAppTheme() {
  return ThemeData(
    useMaterial3: true,
    colorScheme: const ColorScheme.dark(
      background: AppColors.background,
      surface: AppColors.surface,
      primary: AppColors.accent,
      onPrimary: Colors.white,
      onBackground: AppColors.textPrimary,
      onSurface: AppColors.textPrimary,
      error: AppColors.danger,
    ),
    scaffoldBackgroundColor: AppColors.background,
    cardColor: AppColors.panel,
    dividerColor: AppColors.border,
    textTheme: const TextTheme(
      bodyLarge: TextStyle(color: AppColors.textPrimary, fontSize: 14),
      bodyMedium: TextStyle(color: AppColors.textPrimary, fontSize: 13),
      bodySmall: TextStyle(color: AppColors.textSecondary, fontSize: 12),
      titleLarge: TextStyle(
          color: AppColors.textPrimary,
          fontSize: 18,
          fontWeight: FontWeight.w600),
      titleMedium: TextStyle(
          color: AppColors.textPrimary,
          fontSize: 15,
          fontWeight: FontWeight.w500),
      labelSmall: TextStyle(color: AppColors.textMuted, fontSize: 11),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.panel,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: AppColors.border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: AppColors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: AppColors.accent, width: 1.5),
      ),
      hintStyle: const TextStyle(color: AppColors.textMuted),
      contentPadding:
          const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.accent,
        foregroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
        textStyle:
            const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
      ),
    ),
    scrollbarTheme: ScrollbarThemeData(
      thumbColor: MaterialStateProperty.all(AppColors.border),
    ),
  );
}
