import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../app_theme.dart';
import '../services/api_service.dart';
import '../widgets/message_bubble.dart';

class _ChatMessage {
  final String role;
  final String content;
  final DateTime timestamp;

  _ChatMessage({
    required this.role,
    required this.content,
    required this.timestamp,
  });
}

class ChatScreen extends StatefulWidget {
  final ApiService apiService;
  final String sessionId;
  final void Function(String) onSessionChange;

  const ChatScreen({
    super.key,
    required this.apiService,
    required this.sessionId,
    required this.onSessionChange,
  });

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _inputController = TextEditingController();
  final _scrollController = ScrollController();
  final List<_ChatMessage> _messages = [];
  bool _loading = false;
  bool _loadingHistory = false;
  String _agentName = 'ARIA';
  String _error = '';

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  @override
  void didUpdateWidget(ChatScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.sessionId != widget.sessionId) {
      _messages.clear();
      _loadHistory();
    }
  }

Future<void> _loadHistory() async {
    setState(() => _loadingHistory = true);
    try {
      final history = await widget.apiService.getHistory(widget.sessionId);
      if (!mounted) return;
      setState(() {
        _messages.clear();
        for (final msg in history) {
          _messages.add(_ChatMessage(
            role: msg['role'] as String,
            content: msg['content'] as String,
            timestamp: DateTime.parse(msg['timestamp'] as String),
          ));
        }
      });
      _scrollToBottom();
    } catch (_) {
      // History unavailable — start fresh
    } finally {
      if (mounted) setState(() => _loadingHistory = false);
    }
  }

Future<void> _sendMessage() async {
    final text = _inputController.text.trim();
    if (text.isEmpty || _loading) return;

    _inputController.clear();

    setState(() {
      _messages.add(_ChatMessage(
        role: 'user',
        content: text,
        timestamp: DateTime.now(),
      ));
      _loading = true;
      _error = '';
    });

    _scrollToBottom();

    try {
      final history = _messages
          .take(_messages.length - 1)
          .map((m) => {'role': m.role, 'content': m.content})
          .toList();

      final result = await widget.apiService.sendMessage(
        text,
        sessionId: widget.sessionId,
        history: history,
      );

      if (!mounted) return;

      setState(() {
        _agentName = result['agent_name'] as String? ?? _agentName;
        _messages.add(_ChatMessage(
          role: 'assistant',
          content: result['response'] as String? ?? '',
          timestamp: DateTime.now(),
        ));
        _loading = false;
      });

      _scrollToBottom();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString().replaceFirst('Exception: ', '');
        _loading = false;
      });
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _startNewSession() {
    final newId =
        'session_${DateTime.now().millisecondsSinceEpoch}';
    widget.onSessionChange(newId);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Top bar
        Container(
          padding:
              const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          decoration: const BoxDecoration(
            color: AppColors.surface,
            border: Border(bottom: BorderSide(color: AppColors.border)),
          ),
          child: Row(
            children: [
              Container(
                width: 8,
                height: 8,
                decoration: const BoxDecoration(
                  color: AppColors.success,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 10),
              Text(
                _agentName,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.panel,
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: AppColors.border),
                ),
                child: Text(
                  widget.sessionId,
                  style: const TextStyle(
                    color: AppColors.textMuted,
                    fontSize: 11,
                    fontFamily: 'Courier New',
                  ),
                ),
              ),
              const Spacer(),
              TextButton.icon(
                onPressed: _startNewSession,
                icon: const Icon(Icons.add, size: 15),
                label: const Text('New session'),
                style: TextButton.styleFrom(
                  foregroundColor: AppColors.textSecondary,
                  textStyle: const TextStyle(fontSize: 12),
                ),
              ),
              const SizedBox(width: 8),
              IconButton(
                icon: const Icon(Icons.refresh_rounded, size: 18),
                color: AppColors.textSecondary,
                tooltip: 'Reload history',
                onPressed: _loadHistory,
              ),
            ],
          ),
        ),

        // Messages
        Expanded(
          child: _loadingHistory
              ? const Center(
                  child: CircularProgressIndicator(
                      color: AppColors.accent, strokeWidth: 2))
              : _messages.isEmpty
                  ? _buildEmptyState()
                  : ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.fromLTRB(24, 20, 24, 8),
                      itemCount:
                          _messages.length + (_loading ? 1 : 0),
                      itemBuilder: (context, index) {
                        if (index == _messages.length) {
                          return const TypingIndicator();
                        }
                        final msg = _messages[index];
                        return MessageBubble(
                          content: msg.content,
                          isUser: msg.role == 'user',
                          timestamp: DateFormat('HH:mm')
                              .format(msg.timestamp),
                        );
                      },
                    ),
        ),

        // Error banner
        if (_error.isNotEmpty)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(
                horizontal: 20, vertical: 8),
            color: AppColors.danger.withOpacity(0.1),
            child: Row(
              children: [
                const Icon(Icons.error_outline,
                    color: AppColors.danger, size: 15),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _error,
                    style: const TextStyle(
                        color: AppColors.danger, fontSize: 12),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 14),
                  color: AppColors.danger,
                  onPressed: () => setState(() => _error = ''),
                ),
              ],
            ),
          ),

        // Input bar
        Container(
          padding: const EdgeInsets.all(16),
          decoration: const BoxDecoration(
            color: AppColors.surface,
            border: Border(top: BorderSide(color: AppColors.border)),
          ),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _inputController,
                  onSubmitted: (_) => _sendMessage(),
                  maxLines: null,
                  style: const TextStyle(
                      color: AppColors.textPrimary, fontSize: 14),
                  decoration: const InputDecoration(
                    hintText: 'Ask your agent anything...',
                    border: OutlineInputBorder(
                      borderRadius:
                          BorderRadius.all(Radius.circular(8)),
                      borderSide:
                          BorderSide(color: AppColors.border),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              AnimatedContainer(
                duration: const Duration(milliseconds: 150),
                child: ElevatedButton(
                  onPressed: _loading ? null : _sendMessage,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.accent,
                    minimumSize: const Size(48, 48),
                    padding: EdgeInsets.zero,
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8)),
                  ),
                  child: _loading
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white),
                        )
                      : const Icon(Icons.send_rounded,
                          size: 18, color: Colors.white),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.chat_bubble_outline_rounded,
              size: 48,
              color: AppColors.textMuted.withOpacity(0.5)),
          const SizedBox(height: 16),
          const Text(
            'Start a conversation',
            style: TextStyle(
                color: AppColors.textSecondary, fontSize: 15),
          ),
          const SizedBox(height: 8),
          const Text(
            'Try: "create a folder called projects"\nor "what is my RAM usage"',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.textMuted, fontSize: 12),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}