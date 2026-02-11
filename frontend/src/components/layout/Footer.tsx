import React from 'react';

export const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-800 text-gray-300 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          {/* Copyright */}
          <div className="text-sm">
            © {currentYear} Shuren AI. All rights reserved.
          </div>

          {/* Links */}
          <div className="flex space-x-6 text-sm">
            <a
              href="#"
              className="hover:text-white transition-colors"
              onClick={(e) => e.preventDefault()}
            >
              About
            </a>
            <a
              href="#"
              className="hover:text-white transition-colors"
              onClick={(e) => e.preventDefault()}
            >
              Privacy
            </a>
            <a
              href="#"
              className="hover:text-white transition-colors"
              onClick={(e) => e.preventDefault()}
            >
              Terms
            </a>
            <a
              href="#"
              className="hover:text-white transition-colors"
              onClick={(e) => e.preventDefault()}
            >
              Support
            </a>
          </div>

          {/* Version Info */}
          <div className="text-sm text-gray-400">
            Testing Interface v1.0
          </div>
        </div>
      </div>
    </footer>
  );
};
