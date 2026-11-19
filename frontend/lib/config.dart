import 'dart:io';

class ServerConfig {
  static String get baseUrl {
    if (Platform.isAndroid || Platform.isIOS) {
      return 'http://192.168.201.174:8000';
    }
    return 'http://localhost:8000';
  }
}