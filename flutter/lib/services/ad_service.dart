import 'package:flutter/foundation.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

class AdService {
  static final AdService _instance = AdService._();
  factory AdService() => _instance;
  AdService._();

  bool _initialized = false;

  // 테스트 배너 Ad Unit ID (프로덕션 시 교체)
  static const String bannerAdUnitId = 'ca-app-pub-3940256099942544/6300978111';

  Future<void> initialize() async {
    if (_initialized) return;
    await MobileAds.instance.initialize();
    _initialized = true;
    debugPrint('[AdService] AdMob initialized');
  }

  BannerAd createBannerAd({
    required void Function(Ad) onAdLoaded,
    required void Function(Ad, LoadAdError) onAdFailedToLoad,
  }) {
    return BannerAd(
      adUnitId: bannerAdUnitId,
      size: AdSize.banner,
      request: const AdRequest(),
      listener: BannerAdListener(
        onAdLoaded: onAdLoaded,
        onAdFailedToLoad: onAdFailedToLoad,
      ),
    );
  }
}
