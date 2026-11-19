import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../app_theme.dart';

class MessageBubble extends StatelessWidget {
  final String content;
  final bool isUser;
  final String? timestamp;

  const MessageBubble({
    super.key,
    required this.content,
    required this.isUser,
    this.timestamp,
  });

  bool get _isToolOutput =>
      content.contains('Output:\n') ||
      content.contains('Error:\n') ||
      content.startsWith('✅') ||
      content.startsWith('❌') ||
      content.startsWith('🔔') ||
      content.startsWith('📅') ||
      content.startsWith('🖥️') ||
      content.startsWith('🧠') ||
      content.startsWith('💾') ||
      content.startsWith('🔋') ||
      content.startsWith('🌐') ||
      content.startsWith('⚙️');

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.65,
        ),
        margin: const EdgeInsets.only(bottom: 12),
        child: Column(
          crossAxisAlignment:
              isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            // Role label
            Padding(
              padding: const EdgeInsets.only(bottom: 4, left: 4, right: 4),
              child: Text(
                isUser ? 'You' : 'Agent',
                style: const TextStyle(
                  color: AppColors.textMuted,
                  fontSize: 11,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),

            // Bubble
            GestureDetector(
              onLongPress: () {
                Clipboard.setData(ClipboardData(text: content));
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Copied to clipboard'),
                    duration: Duration(seconds: 1),
                    backgroundColor: AppColors.panel,
                  ),
                );
              },
              child: Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: isUser
                      ? AppColors.userBubble
                      : AppColors.agentBubble,
                  borderRadius: BorderRadius.only(
                    topLeft: const Radius.circular(12),
                    topRight: const Radius.circular(12),
                    bottomLeft: Radius.circular(isUser ? 12 : 4),
                    bottomRight: Radius.circular(isUser ? 4 : 12),
                  ),
                  border: Border.all(
                    color: isUser
                        ? AppColors.accentDim.withOpacity(0.4)
                        : AppColors.border,
                  ),
                ),
                child: Text(
                  content,
                  style: TextStyle(
                    color: isUser
                        ? Colors.white
                        : AppColors.textPrimary,
                    fontSize: _isToolOutput ? 12 : 13,
                    fontFamily:
                        _isToolOutput ? 'Courier New' : null,
                    height: 1.5,
                  ),
                ),
              ),
            ),

            if (timestamp != null)
              Padding(
                padding: const EdgeInsets.only(top: 3, left: 4, right: 4),
                child: Text(
                  timestamp!,
                  style: const TextStyle(
                    color: AppColors.textMuted,
                    fontSize: 10,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class TypingIndicator extends StatefulWidget {
  const TypingIndicator({super.key});

  @override
  State<TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<TypingIndicator>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: AppColors.agentBubble,
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(12),
            topRight: Radius.circular(12),
            bottomRight: Radius.circular(12),
            bottomLeft: Radius.circular(4),
          ),
          border: Border.all(color: AppColors.border),
        ),
        child: AnimatedBuilder(
          animation: _controller,
          builder: (context, _) {
            return Row(
              mainAxisSize: MainAxisSize.min,
              children: List.generate(3, (index) {
                final delay = index * 0.33;
                final value = ((_controller.value - delay) % 1.0).clamp(0.0, 1.0);
                final opacity = value < 0.5
                    ? value * 2
                    : (1.0 - value) * 2;
                return Container(
                  margin: const EdgeInsets.symmetric(horizontal: 3),
                  width: 7,
                  height: 7,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppColors.accent.withOpacity(0.3 + opacity * 0.7),
                  ),
                );
              }),
            );
          },
        ),
      ),
    );
  }
}