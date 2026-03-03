import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:path/path.dart' as path;

/// VoiceRoom API 클라이언트
class ApiService {
  // ============================================================
  // 설정 - 실제 환경에 맞게 수정
  // ============================================================
  static const String baseUrl = 'https://goldenrabbit.biz/voiceroom';
  
  String? _token;
  final http.Client _client = http.Client();
  
  /// JWT 토큰 설정
  void setToken(String token) => _token = token;
  String? get token => _token;
  bool get isLoggedIn => _token != null;
  
  /// 인증 헤더
  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (_token != null) 'Authorization': 'Bearer $_token',
  };
  
  // ============================================================
  // 인증
  // ============================================================
  
  /// Google 로그인 (serverAuthCode 포함 시 Drive 연동)
  Future<Map<String, dynamic>> loginWithGoogle(String idToken, {String? serverAuthCode}) async {
    final body = {'id_token': idToken};
    if (serverAuthCode != null) {
      body['server_auth_code'] = serverAuthCode;
    }

    final response = await _client.post(
      Uri.parse('$baseUrl/api/auth/google'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );

    final data = _handleResponse(response);
    _token = data['token'];
    return data;
  }
  
  /// 내 정보
  Future<Map<String, dynamic>> getMe() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/auth/me'),
      headers: _headers,
    );
    return _handleResponse(response);
  }
  
  // ============================================================
  // 채팅방
  // ============================================================
  
  /// 채팅방 목록
  Future<List<dynamic>> getRooms() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/rooms'),
      headers: _headers,
    );
    final data = _handleResponse(response);
    return data['rooms'] ?? [];
  }
  
  /// 채팅방 생성
  Future<Map<String, dynamic>> createRoom(String name, {String? description}) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/rooms'),
      headers: _headers,
      body: jsonEncode({
        'name': name,
        'description': description ?? '',
      }),
    );
    return _handleResponse(response);
  }
  
  /// 채팅방 참여 (초대코드)
  Future<Map<String, dynamic>> joinRoom(String inviteCode) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/rooms/join'),
      headers: _headers,
      body: jsonEncode({'invite_code': inviteCode}),
    );
    return _handleResponse(response);
  }
  
  /// 채팅방 상세
  Future<Map<String, dynamic>> getRoom(int roomId) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/rooms/$roomId'),
      headers: _headers,
    );
    return _handleResponse(response);
  }
  
  // ============================================================
  // 메시지
  // ============================================================
  
  /// 메시지 목록
  Future<List<dynamic>> getMessages(int roomId, {int? beforeId, int limit = 50}) async {
    var url = '$baseUrl/api/rooms/$roomId/messages?limit=$limit';
    if (beforeId != null) url += '&before_id=$beforeId';
    
    final response = await _client.get(Uri.parse(url), headers: _headers);
    final data = _handleResponse(response);
    return data['messages'] ?? [];
  }
  
  /// 텍스트 메시지 전송
  Future<Map<String, dynamic>> sendMessage(int roomId, String content, {int? parentId}) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/rooms/$roomId/messages'),
      headers: _headers,
      body: jsonEncode({
        'content': content,
        if (parentId != null) 'parent_id': parentId,
      }),
    );
    return _handleResponse(response);
  }
  
  /// 음성 파일 업로드
  Future<Map<String, dynamic>> uploadAudio(int roomId, File audioFile, {String language = 'ko'}) async {
    final uri = Uri.parse('$baseUrl/api/rooms/$roomId/audio');
    final request = http.MultipartRequest('POST', uri);
    
    request.headers['Authorization'] = 'Bearer $_token';
    request.fields['language'] = language;
    request.files.add(
      await http.MultipartFile.fromPath('file', audioFile.path,
        filename: path.basename(audioFile.path)),
    );
    
    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    return _handleResponse(response);
  }
  
  /// 음성 파일 검색
  Future<List<dynamic>> searchAudio(int roomId, {
    String? phone, String? dateFrom, String? dateTo,
  }) async {
    var url = '$baseUrl/api/rooms/$roomId/audio/search?';
    if (phone != null) url += 'phone=$phone&';
    if (dateFrom != null) url += 'date_from=$dateFrom&';
    if (dateTo != null) url += 'date_to=$dateTo&';
    
    final response = await _client.get(Uri.parse(url), headers: _headers);
    final data = _handleResponse(response);
    return data['audio_files'] ?? [];
  }
  
  /// 음성 파일 상세
  Future<Map<String, dynamic>> getAudioDetail(int audioId) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/audio/$audioId'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  /// 음성 파일 다운로드 URL
  String getAudioDownloadUrl(int audioId) {
    return '$baseUrl/api/audio/$audioId/download';
  }

  /// 음성 파일 다운로드 (바이트로 반환)
  Future<List<int>> downloadAudio(int audioId) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/audio/$audioId/download'),
      headers: _headers,
    );
    if (response.statusCode == 200) {
      return response.bodyBytes;
    }
    throw ApiException('다운로드 실패', response.statusCode);
  }
  
  // ============================================================
  // 멤버 승인/거절
  // ============================================================

  /// 채팅방 삭제
  Future<Map<String, dynamic>> deleteRoom(int roomId) async {
    final response = await _client.delete(
      Uri.parse('$baseUrl/api/rooms/$roomId'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  /// 채팅방 이름 변경
  Future<Map<String, dynamic>> renameRoom(int roomId, String newName) async {
    final response = await _client.patch(
      Uri.parse('$baseUrl/api/rooms/$roomId'),
      headers: _headers,
      body: jsonEncode({'name': newName}),
    );
    return _handleResponse(response);
  }

  /// 채팅방 나가기
  Future<Map<String, dynamic>> leaveRoom(int roomId) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/rooms/$roomId/leave'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  /// 관리자 권한 이전
  Future<Map<String, dynamic>> transferAdmin(int roomId, int newAdminId) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/rooms/$roomId/transfer-admin'),
      headers: _headers,
      body: jsonEncode({'user_id': newAdminId}),
    );
    return _handleResponse(response);
  }

  /// 즐겨찾기 토글
  Future<Map<String, dynamic>> toggleFavorite(int roomId) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/rooms/$roomId/favorite'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  /// 멤버 승인
  Future<Map<String, dynamic>> approveMember(int roomId, int userId) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/rooms/$roomId/members/$userId/approve'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  /// 멤버 거절
  Future<Map<String, dynamic>> rejectMember(int roomId, int userId) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/rooms/$roomId/members/$userId/reject'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  // ============================================================
  // 동의 관리
  // ============================================================

  /// 동의 기록 저장
  Future<Map<String, dynamic>> recordConsent(List<Map<String, String>> consents) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/auth/consent'),
      headers: _headers,
      body: jsonEncode({'consents': consents}),
    );
    return _handleResponse(response);
  }

  /// 동의 상태 조회
  Future<Map<String, dynamic>> getConsentStatus() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/auth/consent/status'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  /// 동의 철회
  Future<Map<String, dynamic>> withdrawConsent(String consentType) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/auth/consent/withdraw'),
      headers: _headers,
      body: jsonEncode({'type': consentType}),
    );
    return _handleResponse(response);
  }

  /// 회원 탈퇴
  Future<Map<String, dynamic>> deleteAccount() async {
    final response = await _client.delete(
      Uri.parse('$baseUrl/api/auth/account'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  // ============================================================
  // Drive 연동
  // ============================================================

  /// Drive 연동 상태 확인
  Future<Map<String, dynamic>> getDriveStatus() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/auth/drive/status'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  /// Drive 연동 해제
  Future<Map<String, dynamic>> disconnectDrive() async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/auth/drive/disconnect'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  // ============================================================
  // 응답 처리
  // ============================================================
  Map<String, dynamic> _handleResponse(http.Response response) {
    final data = jsonDecode(response.body);
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return data;
    }
    throw ApiException(
      data['error'] ?? '알 수 없는 오류',
      response.statusCode,
    );
  }
  
  void dispose() => _client.close();
}

class ApiException implements Exception {
  final String message;
  final int statusCode;
  ApiException(this.message, this.statusCode);
  
  @override
  String toString() => 'ApiException($statusCode): $message';
}
