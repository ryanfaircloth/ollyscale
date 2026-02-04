import { Dropdown } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';

interface LanguageOption {
  code: string;
  name: string;
  flag: string;
}

const languages: LanguageOption[] = [
  { code: 'en-US', name: 'English (US)', flag: '🇺🇸' },
  { code: 'en-GB', name: 'English (UK)', flag: '🇬🇧' },
];

export default function LanguageSelector() {
  const { i18n } = useTranslation();

  const currentLanguage = languages.find((lang) => lang.code === i18n.language) || languages[0];

  const handleLanguageChange = (languageCode: string) => {
    i18n.changeLanguage(languageCode);
  };

  return (
    <Dropdown>
      <Dropdown.Toggle variant="outline-secondary" size="sm" id="language-selector">
        <span className="me-1">{currentLanguage.flag}</span>
        <span className="d-none d-md-inline">{currentLanguage.name}</span>
      </Dropdown.Toggle>

      <Dropdown.Menu>
        {languages.map((lang) => (
          <Dropdown.Item
            key={lang.code}
            active={lang.code === i18n.language}
            onClick={() => handleLanguageChange(lang.code)}
          >
            <span className="me-2">{lang.flag}</span>
            {lang.name}
          </Dropdown.Item>
        ))}
      </Dropdown.Menu>
    </Dropdown>
  );
}
