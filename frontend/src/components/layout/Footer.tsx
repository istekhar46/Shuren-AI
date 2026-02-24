import React from 'react';

export const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer
      className="mt-auto border-t"
      style={{ background: 'var(--color-bg-primary)', borderColor: 'var(--color-border)' }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          {/* Copyright */}
          <div className="text-sm" style={{ color: 'var(--color-text-faint)' }}>
            © {currentYear} Shuren AI. All rights reserved.
          </div>

          {/* Links */}
          <div className="flex space-x-6 text-sm">
            {['About', 'Privacy', 'Terms', 'Support'].map((label) => (
              <a
                key={label}
                href="#"
                className="transition-colors"
                style={{ color: 'var(--color-text-muted)' }}
                onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--color-text-primary)')}
                onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--color-text-muted)')}
                onClick={(e) => e.preventDefault()}
              >
                {label}
              </a>
            ))}
          </div>

          {/* Version */}
          <div className="text-sm" style={{ color: 'var(--color-text-faint)' }}>
            Testing Interface v1.0
          </div>
        </div>
      </div>
    </footer>
  );
};
