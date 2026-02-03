import { Nav, Button, Tooltip, OverlayTrigger } from 'react-bootstrap';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@/contexts/ThemeContext';
import { useRefresh } from '@/contexts/RefreshContext';
import { useLocalStorage } from '@/hooks/useLocalStorage';
import LanguageSelector from '@/components/common/LanguageSelector';

export default function Sidebar() {
  const { t } = useTranslation();
  const { theme, setTheme } = useTheme();
  const { enabled: refreshEnabled, toggle: toggleRefresh } = useRefresh();
  const [collapsed, setCollapsed] = useLocalStorage('sidebar-collapsed', false);

  const toggleCollapsed = () => setCollapsed(!collapsed);

  const navItems = [
    { to: '/dashboard', icon: 'speedometer2', labelKey: 'nav.dashboard' },
    { to: '/logs', icon: 'file-text', labelKey: 'nav.logs' },
    { to: '/metrics', icon: 'bar-chart', labelKey: 'nav.metrics' },
    { to: '/traces', icon: 'activity', labelKey: 'nav.traces' },
    { to: '/spans', icon: 'layers', labelKey: 'nav.spans' },
    { to: '/catalog', icon: 'book', labelKey: 'nav.catalog' },
    { to: '/map', icon: 'diagram-3', labelKey: 'nav.map' },
    { to: '/ai-agents', icon: 'robot', labelKey: 'nav.aiAgents' },
    { to: '/collector', icon: 'hash', labelKey: 'nav.otelConfig' },
  ];

  return (
    <div
      className="d-flex flex-column bg-body-tertiary border-end transition-all"
      style={{ width: collapsed ? '70px' : '250px', transition: 'width 0.2s ease' }}
    >
      {/* Logo/Brand */}
      <div className="p-3 border-bottom d-flex align-items-center justify-content-between" style={{ height: '64px' }}>
        <div className="d-flex align-items-center gap-2" style={{ overflow: 'hidden' }}>
          <img src="/logo.svg" alt={t('app.title')} style={{ height: '32px', width: '32px', flexShrink: 0 }} />
          {!collapsed && <h4 className="mb-0" style={{ whiteSpace: 'nowrap' }}>{t('app.title')}</h4>}
        </div>
        <Button
          variant="link"
          size="sm"
          onClick={toggleCollapsed}
          className="text-body p-0"
          style={{ minWidth: 'auto' }}
          title={t(collapsed ? 'sidebar.expand' : 'sidebar.collapse')}
        >
          <i className={`bi bi-${collapsed ? 'chevron-right' : 'chevron-left'}`}></i>
        </Button>
      </div>

      {/* Navigation */}
      <Nav className="flex-column flex-grow-1 p-2" as="nav">
        {navItems.map((item) => {
          const label = t(item.labelKey);
          const navLink = (
            <Nav.Link
              as={NavLink}
              to={item.to}
              className="mb-1 rounded"
              style={{
                padding: collapsed ? '0.5rem' : '0.5rem 0.75rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: collapsed ? 'center' : 'flex-start',
              }}
            >
              <i className={`bi bi-${item.icon}`} style={{ fontSize: '1.2rem' }}></i>
              {!collapsed && <span className="ms-2">{label}</span>}
            </Nav.Link>
          );

          // Show tooltip only when collapsed
          if (collapsed) {
            return (
              <OverlayTrigger
                key={item.to}
                placement="right"
                overlay={<Tooltip>{label}</Tooltip>}
              >
                {navLink}
              </OverlayTrigger>
            );
          }

          return <div key={item.to}>{navLink}</div>;
        })}
      </Nav>

      {/* Controls */}
      <div className="p-3 border-top">
        {!collapsed ? (
          <>
            {/* Language selector */}
            <div className="mb-3">
              <LanguageSelector />
            </div>

            {/* Auto-refresh toggle */}
            <div className="form-check form-switch mb-3">
              <input
                className="form-check-input"
                type="checkbox"
                id="autoRefreshSwitch"
                checked={refreshEnabled}
                onChange={toggleRefresh}
              />
              <label className="form-check-label" htmlFor="autoRefreshSwitch">
                {t('sidebar.autoRefresh')}
              </label>
            </div>

            {/* Manual refresh button (shown when auto-refresh is off) */}
            {!refreshEnabled && (
              <Button
                variant="outline-primary"
                size="sm"
                className="w-100 mb-3"
                onClick={() => window.location.reload()}
              >
                <i className="bi bi-arrow-clockwise me-1"></i>
                {t('sidebar.refreshNow')}
              </Button>
            )}

            {/* Theme selector */}
            <div className="mb-2">
              <label className="form-label small">{t('sidebar.theme')}</label>
              <select
                className="form-select form-select-sm"
                value={theme}
                onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'auto')}
              >
                <option value="light">{t('theme.light')}</option>
                <option value="dark">{t('theme.dark')}</option>
                <option value="auto">{t('theme.auto')}</option>
              </select>
            </div>
          </>
        ) : (
          <div className="d-flex flex-column align-items-center gap-2">
            {/* Language selector (icon only) */}
            <LanguageSelector />

            {/* Auto-refresh icon */}
            <OverlayTrigger
              placement="right"
              overlay={<Tooltip>{t('sidebar.autoRefresh')} {refreshEnabled ? t('common.on') : t('common.off')}</Tooltip>}
            >
              <Button
                variant={refreshEnabled ? 'success' : 'secondary'}
                size="sm"
                onClick={toggleRefresh}
                style={{ width: '36px', height: '36px', padding: 0 }}
              >
                <i className={`bi bi-arrow-${refreshEnabled ? 'repeat' : 'pause'}`}></i>
              </Button>
            </OverlayTrigger>

            {/* Manual refresh button (shown when auto-refresh is off) */}
            {!refreshEnabled && (
              <OverlayTrigger placement="right" overlay={<Tooltip>{t('sidebar.refreshNow')}</Tooltip>}>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => window.location.reload()}
                  style={{ width: '36px', height: '36px', padding: 0 }}
                >
                  <i className="bi bi-arrow-clockwise"></i>
                </Button>
              </OverlayTrigger>
            )}

            {/* Theme icon */}
            <OverlayTrigger
              placement="right"
              overlay={<Tooltip>{t('sidebar.theme')}: {t(`theme.${theme}`)}</Tooltip>}
            >
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  const themes = ['light', 'dark', 'auto'] as const;
                  const currentIndex = themes.indexOf(theme);
                  const nextTheme = themes[(currentIndex + 1) % themes.length];
                  setTheme(nextTheme);
                }}
                style={{ width: '36px', height: '36px', padding: 0 }}
              >
                <i className={`bi bi-${theme === 'dark' ? 'moon-stars' : theme === 'light' ? 'sun' : 'circle-half'}`}></i>
              </Button>
            </OverlayTrigger>
          </div>
        )}
      </div>
    </div>
  );
}
