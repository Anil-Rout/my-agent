import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../services/api_service.dart';

class ApprovalsScreen extends StatefulWidget {
  final ApiService apiService;
  final String sessionId;

  const ApprovalsScreen({
    super.key,
    required this.apiService,
    required this.sessionId,
  });

  @override
  State<ApprovalsScreen> createState() => _ApprovalsScreenState();
}

class _ApprovalsScreenState extends State<ApprovalsScreen> {
  List<dynamic> _approvals = [];
  bool _loading = true;
  String? _error;
  late String _sessionId;
  late TextEditingController _sessionController;

  @override
  void initState() {
    super.initState();
    _sessionId = widget.sessionId;
    _sessionController = TextEditingController(text: _sessionId);
    _load();
  }

  @override
  void didUpdateWidget(ApprovalsScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.sessionId != widget.sessionId) {
      _sessionId = widget.sessionId;
      _sessionController.text = _sessionId;
      _load();
    }
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final approvals = await widget.apiService.getApprovals(_sessionId);
      setState(() {
        _approvals = approvals;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString().replaceFirst('Exception: ', '');
        _loading = false;
      });
    }
  }

  Future<void> _approve(int approvalId) async {
    try {
      await widget.apiService.approveAction(approvalId);
      _showSnack('Action approved', AppColors.success);
      _load();
    } catch (e) {
      _showSnack('Failed to approve', AppColors.danger);
    }
  }

  Future<void> _deny(int approvalId) async {
    try {
      await widget.apiService.denyAction(approvalId);
      _showSnack('Action denied', AppColors.warning);
      _load();
    } catch (e) {
      _showSnack('Failed to deny', AppColors.danger);
    }
  }

  void _showSnack(String message, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message,
            style: const TextStyle(color: Colors.white)),
        backgroundColor: color,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  String _describeTool(String toolName, Map<String, dynamic> args) {
    switch (toolName) {
      case 'tool_delete_file':
        return 'Delete: ${args['filepath'] ?? args['path'] ?? 'unknown path'}';
      case 'tool_shutdown':
        return 'Shutdown PC in ${args['delay_seconds'] ?? 30} seconds';
      case 'tool_restart':
        return 'Restart PC in ${args['delay_seconds'] ?? 30} seconds';
      case 'tool_kill_process':
        return 'Kill process: ${args['process_name'] ?? 'unknown'}';
      case 'tool_install_package':
        return 'Install package: ${args['package_name'] ?? 'unknown'}';
      default:
        return toolName;
    }
  }

  IconData _toolIcon(String toolName) {
    if (toolName.contains('delete')) return Icons.delete_outline_rounded;
    if (toolName.contains('shutdown')) return Icons.power_settings_new_rounded;
    if (toolName.contains('restart')) return Icons.restart_alt_rounded;
    if (toolName.contains('kill')) return Icons.stop_circle_outlined;
    if (toolName.contains('install')) return Icons.download_rounded;
    return Icons.warning_amber_rounded;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Header
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          decoration: const BoxDecoration(
            color: AppColors.surface,
            border: Border(bottom: BorderSide(color: AppColors.border)),
          ),
          child: Row(
            children: [
              const Icon(Icons.warning_amber_rounded,
                  color: AppColors.warning, size: 16),
              const SizedBox(width: 8),
              const Text(
                'Pending Approvals',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
              if (_approvals.isNotEmpty) ...[
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 7, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppColors.warning.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                        color: AppColors.warning.withOpacity(0.3)),
                  ),
                  child: Text(
                    '${_approvals.length}',
                    style: const TextStyle(
                      color: AppColors.warning,
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
              const Spacer(),
              IconButton(
                icon: const Icon(Icons.refresh_rounded, size: 18),
                color: AppColors.textSecondary,
                onPressed: _load,
                tooltip: 'Refresh',
              ),
            ],
          ),
        ),

        // Session ID input
        Container(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
          decoration: const BoxDecoration(
            color: AppColors.panel,
            border: Border(bottom: BorderSide(color: AppColors.border)),
          ),
          child: Row(
            children: [
              const Text(
                'Session:',
                style: TextStyle(
                    color: AppColors.textSecondary, fontSize: 12),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: TextField(
                  controller: _sessionController,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 12,
                    fontFamily: 'Courier New',
                  ),
                  decoration: const InputDecoration(
                    isDense: true,
                    contentPadding: EdgeInsets.symmetric(
                        horizontal: 10, vertical: 8),
                  ),
                  onSubmitted: (val) {
                    _sessionId = val.trim();
                    _load();
                  },
                ),
              ),
              const SizedBox(width: 8),
              TextButton(
                onPressed: () {
                  _sessionId = _sessionController.text.trim();
                  _load();
                },
                style: TextButton.styleFrom(
                    foregroundColor: AppColors.accent,
                    textStyle: const TextStyle(fontSize: 12)),
                child: const Text('Load'),
              ),
            ],
          ),
        ),

        // Content
        Expanded(
          child: _loading
              ? const Center(
                  child: CircularProgressIndicator(
                      color: AppColors.accent, strokeWidth: 2))
              : _error != null
                  ? _buildError()
                  : _approvals.isEmpty
                      ? _buildEmpty()
                      : ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _approvals.length,
                          itemBuilder: (context, index) {
                            return _buildApprovalCard(
                                _approvals[index]);
                          },
                        ),
        ),
      ],
    );
  }

  Widget _buildApprovalCard(Map<String, dynamic> approval) {
    final id = approval['id'] as int;
    final toolName = approval['tool_name'] as String? ?? '';
    final args = (approval['tool_args'] as Map<String, dynamic>?) ?? {};
    final reason = approval['reason'] as String? ?? '';

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.warning.withOpacity(0.3)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Tool name and icon
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppColors.warning.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                        color: AppColors.warning.withOpacity(0.3)),
                  ),
                  child: Icon(_toolIcon(toolName),
                      color: AppColors.warning, size: 18),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _describeTool(toolName, args),
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontWeight: FontWeight.w600,
                          fontSize: 13,
                        ),
                      ),
                      Text(
                        toolName,
                        style: const TextStyle(
                          color: AppColors.textMuted,
                          fontSize: 11,
                          fontFamily: 'Courier New',
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),

            if (reason.isNotEmpty) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.panel,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  reason,
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12,
                  ),
                ),
              ),
            ],

            const SizedBox(height: 14),

            // Args preview
            if (args.isNotEmpty) ...[
              const Text(
                'Arguments',
                style: TextStyle(
                    color: AppColors.textMuted, fontSize: 11),
              ),
              const SizedBox(height: 4),
              ...args.entries.map((e) => Padding(
                    padding: const EdgeInsets.only(bottom: 2),
                    child: Row(
                      children: [
                        Text(
                          '${e.key}: ',
                          style: const TextStyle(
                            color: AppColors.textMuted,
                            fontSize: 11,
                            fontFamily: 'Courier New',
                          ),
                        ),
                        Text(
                          '${e.value}',
                          style: const TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 11,
                            fontFamily: 'Courier New',
                          ),
                        ),
                      ],
                    ),
                  )),
              const SizedBox(height: 12),
            ],

            // Action buttons
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _deny(id),
                    icon: const Icon(Icons.close_rounded, size: 15),
                    label: const Text('Deny'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.danger,
                      side: BorderSide(
                          color: AppColors.danger.withOpacity(0.4)),
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      textStyle: const TextStyle(fontSize: 13),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => _approve(id),
                    icon: const Icon(Icons.check_rounded, size: 15),
                    label: const Text('Approve'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.success,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      textStyle: const TextStyle(fontSize: 13),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmpty() {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.check_circle_outline_rounded,
              size: 48, color: AppColors.success),
          SizedBox(height: 12),
          Text('No pending approvals',
              style: TextStyle(color: AppColors.textSecondary)),
          SizedBox(height: 6),
          Text(
            'Dangerous actions like delete, shutdown,\nand install will appear here for review',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.textMuted, fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.error_outline, color: AppColors.danger, size: 36),
          const SizedBox(height: 12),
          Text(_error!,
              style: const TextStyle(color: AppColors.textSecondary)),
          const SizedBox(height: 16),
          ElevatedButton(onPressed: _load, child: const Text('Retry')),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _sessionController.dispose();
    super.dispose();
  }
}