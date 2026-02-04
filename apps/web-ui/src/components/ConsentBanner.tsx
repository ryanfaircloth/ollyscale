import { useState, useEffect } from 'react';
import { Alert, Button } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { initializeTelemetry } from '@/telemetry/config';

const CONSENT_KEY = 'ollyscale-telemetry-consent';
const CONSENT_BANNER_DISMISSED_KEY = 'ollyscale-telemetry-banner-dismissed';

export function ConsentBanner() {
  const { t } = useTranslation();
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    // Check if user has already seen and dismissed the banner
    const bannerDismissed = localStorage.getItem(CONSENT_BANNER_DISMISSED_KEY);
    const consentGiven = localStorage.getItem(CONSENT_KEY);

    // Show banner if user hasn't made a choice yet
    if (!bannerDismissed && !consentGiven) {
      setShowBanner(true);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem(CONSENT_KEY, 'true');
    localStorage.setItem(CONSENT_BANNER_DISMISSED_KEY, 'true');
    setShowBanner(false);

    // Initialize telemetry now that consent is given
    initializeTelemetry();
  };

  const handleDecline = () => {
    localStorage.setItem(CONSENT_KEY, 'false');
    localStorage.setItem(CONSENT_BANNER_DISMISSED_KEY, 'true');
    setShowBanner(false);
  };

  if (!showBanner) {
    return null;
  }

  return (
    <Alert
      variant="info"
      dismissible={false}
      className="position-fixed bottom-0 start-0 m-3 shadow-lg"
      style={{ maxWidth: '500px', zIndex: 9999 }}
    >
      <Alert.Heading className="h6">
        <i className="bi bi-info-circle me-2"></i>
        {t('consent.title')}
      </Alert.Heading>
      <p className="small mb-3">
        {t('consent.description')}
      </p>
      <ul className="small mb-3">
        <li>{t('consent.dataPoints.performance')}</li>
        <li>{t('consent.dataPoints.navigation')}</li>
        <li>{t('consent.dataPoints.apiTimes')}</li>
      </ul>
      <p className="small mb-3">
        <strong>{t('consent.noPersonalData')}</strong> {t('consent.changeAnytime')}
      </p>
      <div className="d-flex gap-2">
        <Button variant="primary" size="sm" onClick={handleAccept}>
          <i className="bi bi-check-circle me-1"></i>
          {t('consent.accept')}
        </Button>
        <Button variant="outline-secondary" size="sm" onClick={handleDecline}>
          <i className="bi bi-x-circle me-1"></i>
          {t('consent.decline')}
        </Button>
      </div>
    </Alert>
  );
}
