import 'dart:io';
import 'package:flutter/material.dart';
import 'package:path/path.dart' as path;
import 'package:permission_handler/permission_handler.dart';

/// 녹음 파일 선택 화면 - 최신순 정렬
class AudioPickerScreen extends StatefulWidget {
  const AudioPickerScreen({super.key});

  @override
  State<AudioPickerScreen> createState() => _AudioPickerScreenState();
}

class _AudioPickerScreenState extends State<AudioPickerScreen> {
  List<FileSystemEntity> _audioFiles = [];
  bool _isLoading = true;
  String? _errorMessage;
  String _currentPath = '';
  bool _showPermissionDenied = false;

  // 지원하는 오디오 확장자
  static const _audioExtensions = [
    '.mp3', '.wav', '.ogg', '.m4a', '.flac', '.webm', '.mp4', '.aac', '.amr', '.3gp'
  ];

  // 검색할 녹음 폴더 경로들 (통신사/제조사별)
  static const _recordingPaths = [
    // 삼성 기본 전화 통화녹음
    '/storage/emulated/0/Recordings/Call',
    '/storage/emulated/0/Call',
    // 에이닷/T전화 (SKT) - OS 12 이상
    '/storage/emulated/0/Recordings/TPhoneCallRecords',
    // 에이닷/T전화 - OS 12 미만
    '/storage/emulated/0/Music/TPhoneCallRecords',
    '/storage/emulated/0/Music/TPhoneCallRecords/my_sounds',
    // 삼성 음성녹음 앱
    '/storage/emulated/0/Recordings/Voice Recorder',
    '/storage/emulated/0/Recordings',
    '/storage/emulated/0/Samsung/Voice Recorder',
    '/storage/emulated/0/DCIM/Voice Recorder',
    // LG 통화녹음
    '/storage/emulated/0/CallRecord',
    '/storage/emulated/0/LGCallRecording',
    // KT/LGU+ 기본 전화
    '/storage/emulated/0/PhoneRecord',
    '/storage/emulated/0/Record',
    // 기타
    '/storage/emulated/0/Download',
    '/storage/emulated/0/Music',
  ];

  @override
  void initState() {
    super.initState();
    _loadAudioFiles();
  }

  Future<void> _loadAudioFiles() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      // 권한 확인
      var status = await Permission.storage.status;
      if (!status.isGranted) {
        status = await Permission.storage.request();
      }

      // Android 11+ 에서는 manageExternalStorage 권한 필요
      if (Platform.isAndroid) {
        var manageStatus = await Permission.manageExternalStorage.status;
        if (!manageStatus.isGranted) {
          manageStatus = await Permission.manageExternalStorage.request();
        }

        // 권한이 거부된 경우
        if (!manageStatus.isGranted) {
          setState(() {
            _errorMessage = '파일 접근 권한이 필요합니다.\n설정에서 "모든 파일 접근" 권한을 허용해주세요.';
            _isLoading = false;
            _showPermissionDenied = true;
          });
          return;
        }
      }

      List<FileSystemEntity> allFiles = [];

      // 각 경로에서 오디오 파일 검색
      for (final dirPath in _recordingPaths) {
        final dir = Directory(dirPath);
        if (await dir.exists()) {
          _currentPath = dirPath;
          final files = await _scanDirectory(dir);
          allFiles.addAll(files);
        }
      }

      // 중복 제거 (경로 기준)
      final uniqueFiles = <String, FileSystemEntity>{};
      for (final file in allFiles) {
        uniqueFiles[file.path] = file;
      }

      // 최신순 정렬 (수정일 기준)
      final sortedFiles = uniqueFiles.values.toList();
      sortedFiles.sort((a, b) {
        final aStat = a.statSync();
        final bStat = b.statSync();
        return bStat.modified.compareTo(aStat.modified); // 최신순
      });

      setState(() {
        _audioFiles = sortedFiles;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = '파일을 불러오는 중 오류: $e';
        _isLoading = false;
      });
    }
  }

  Future<List<FileSystemEntity>> _scanDirectory(Directory dir) async {
    List<FileSystemEntity> audioFiles = [];

    try {
      await for (final entity in dir.list(recursive: true, followLinks: false)) {
        if (entity is File) {
          final ext = path.extension(entity.path).toLowerCase();
          if (_audioExtensions.contains(ext)) {
            audioFiles.add(entity);
          }
        }
      }
    } catch (e) {
      // 권한 없는 폴더는 무시
    }

    return audioFiles;
  }

  String _formatFileSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inDays == 0) {
      return '오늘 ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
    } else if (diff.inDays == 1) {
      return '어제';
    } else if (diff.inDays < 7) {
      return '${diff.inDays}일 전';
    } else {
      return '${date.month}/${date.day}';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('녹음 파일 선택'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadAudioFiles,
            tooltip: '새로고침',
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('녹음 파일을 검색 중...'),
          ],
        ),
      );
    }

    if (_errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                _showPermissionDenied ? Icons.folder_off : Icons.error_outline,
                size: 64,
                color: _showPermissionDenied ? Colors.orange : Colors.red,
              ),
              const SizedBox(height: 16),
              Text(_errorMessage!, textAlign: TextAlign.center),
              const SizedBox(height: 24),
              if (_showPermissionDenied) ...[
                ElevatedButton.icon(
                  onPressed: () async {
                    final status = await Permission.manageExternalStorage.request();
                    if (status.isGranted) {
                      _loadAudioFiles();
                    }
                  },
                  icon: const Icon(Icons.folder_open),
                  label: const Text('파일 접근 권한 허용'),
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(220, 48),
                  ),
                ),
                const SizedBox(height: 16),
              ],
              OutlinedButton(
                onPressed: _loadAudioFiles,
                child: const Text('다시 시도'),
              ),
            ],
          ),
        ),
      );
    }

    if (_audioFiles.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.audio_file, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            const Text('녹음 파일을 찾을 수 없습니다'),
            const SizedBox(height: 8),
            Text(
              '검색 위치: ${_recordingPaths.join(", ")}',
              style: const TextStyle(fontSize: 12, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadAudioFiles,
              child: const Text('다시 검색'),
            ),
          ],
        ),
      );
    }

    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          color: Colors.grey[100],
          child: Row(
            children: [
              const Icon(Icons.info_outline, size: 16, color: Colors.grey),
              const SizedBox(width: 8),
              Text(
                '${_audioFiles.length}개 파일 (최신순)',
                style: const TextStyle(color: Colors.grey),
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView.builder(
            itemCount: _audioFiles.length,
            itemBuilder: (context, index) {
              final file = _audioFiles[index] as File;
              final stat = file.statSync();
              final fileName = path.basename(file.path);

              return ListTile(
                leading: const CircleAvatar(
                  child: Icon(Icons.audio_file),
                ),
                title: Text(
                  fileName,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                subtitle: Text(
                  '${_formatFileSize(stat.size)} · ${_formatDate(stat.modified)}',
                ),
                trailing: const Icon(Icons.chevron_right),
                onTap: () {
                  Navigator.pop(context, file);
                },
              );
            },
          ),
        ),
      ],
    );
  }
}
