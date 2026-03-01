import React, { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import logo from '../assets/logo.png';
import './LandingPage.css';

/* ─── Feature data ─── */
const FEATURES = [
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="h-7 w-7">
        <path d="M6.5 6.5h3v11h-3zM14.5 3.5h3v14h-3z" stroke="url(#gf)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M2 20.5h20" stroke="url(#gf)" strokeWidth="1.5" strokeLinecap="round" />
        <defs><linearGradient id="gf" x1="2" y1="3.5" x2="22" y2="20.5" gradientUnits="userSpaceOnUse"><stop stopColor="#a78bfa" /><stop offset="1" stopColor="#f472b6" /></linearGradient></defs>
      </svg>
    ),
    title: 'Workout Planning',
    description: 'Personalized routines designed for your exact fitness level — from beginner to advanced.',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="h-7 w-7">
        <circle cx="12" cy="12" r="9" stroke="url(#gf2)" strokeWidth="1.5" />
        <path d="M12 8v4l2.5 2.5" stroke="url(#gf2)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M8 3l1 2M16 3l-1 2" stroke="url(#gf2)" strokeWidth="1.5" strokeLinecap="round" />
        <defs><linearGradient id="gf2" x1="3" y1="3" x2="21" y2="21" gradientUnits="userSpaceOnUse"><stop stopColor="#a78bfa" /><stop offset="1" stopColor="#f472b6" /></linearGradient></defs>
      </svg>
    ),
    title: 'Diet Planning',
    description: 'Meal plans respecting your preferences, allergies & macros — never boring, always delicious.',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="h-7 w-7">
        <rect x="4" y="4" width="16" height="16" rx="3" stroke="url(#gf3)" strokeWidth="1.5" />
        <path d="M4 12h4l2-4 4 8 2-4h4" stroke="url(#gf3)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        <defs><linearGradient id="gf3" x1="4" y1="4" x2="20" y2="20" gradientUnits="userSpaceOnUse"><stop stopColor="#a78bfa" /><stop offset="1" stopColor="#f472b6" /></linearGradient></defs>
      </svg>
    ),
    title: 'Smart Tracking',
    description: 'Auto-adjusts your plan when life gets in the way. Miss a session? Zero guilt, just adaptation.',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="h-7 w-7">
        <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" stroke="url(#gf4)" strokeWidth="1.5" strokeLinecap="round" />
        <circle cx="12" cy="12" r="4" stroke="url(#gf4)" strokeWidth="1.5" />
        <defs><linearGradient id="gf4" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse"><stop stopColor="#a78bfa" /><stop offset="1" stopColor="#f472b6" /></linearGradient></defs>
      </svg>
    ),
    title: 'Supplement Guidance',
    description: 'Non-medical, goal-aligned advice in plain language — optional, not required.',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="h-7 w-7">
        <path d="M5 12l5 5L20 7" stroke="url(#gf5)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M3 6h18M3 18h18" stroke="url(#gf5)" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
        <defs><linearGradient id="gf5" x1="3" y1="6" x2="20" y2="18" gradientUnits="userSpaceOnUse"><stop stopColor="#a78bfa" /><stop offset="1" stopColor="#f472b6" /></linearGradient></defs>
      </svg>
    ),
    title: 'Reminders & Scheduling',
    description: 'Timely nudges for workouts, meals & hydration that inform — never pressure.',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="h-7 w-7">
        <path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.66 0 3-4.03 3-9s-1.34-9-3-9m0 18c-1.66 0-3-4.03-3-9s1.34-9 3-9m-9 9a9 9 0 019-9" stroke="url(#gf6)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        <defs><linearGradient id="gf6" x1="3" y1="3" x2="21" y2="21" gradientUnits="userSpaceOnUse"><stop stopColor="#a78bfa" /><stop offset="1" stopColor="#f472b6" /></linearGradient></defs>
      </svg>
    ),
    title: 'AI Coach — Chat',
    description: 'Your coach understands context, adapts in real-time, and keeps you moving.',
  },
] as const;

/* Stats */
const STATS = [
  { value: '6', label: 'Specialized AI Agents' },
  { value: '24/7', label: 'Always Available' },
  { value: '100%', label: 'Personalized Plans' },
  { value: '0', label: 'Guilt or Pressure' },
];

/* ─── Intersection Observer reveal hook ─── */
function useReveal() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { el.classList.add('ds-reveal--visible'); obs.unobserve(el); } },
      { threshold: 0.12 },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return ref;
}

const Reveal: React.FC<{ children: React.ReactNode; className?: string; delay?: number }> = ({ children, className = '', delay = 0 }) => {
  const ref = useReveal();
  return <div ref={ref} className={`ds-reveal ${className}`} style={delay ? { transitionDelay: `${delay}ms` } : undefined}>{children}</div>;
};

/* ═══════════════════════════════════════════════ */
/*              LANDING PAGE COMPONENT             */
/* ═══════════════════════════════════════════════ */
export const LandingPage: React.FC = () => {
  return (
    <div className="landing-root">
      {/* ── Animated aurora background ── */}
      <div aria-hidden="true" className="landing-aurora">
        <div className="landing-orb landing-orb--1" />
        <div className="landing-orb landing-orb--2" />
        <div className="landing-orb landing-orb--3" />
        <div className="landing-orb landing-orb--4" />
      </div>

      {/* ── Noise texture overlay ── */}
      <div aria-hidden="true" className="landing-noise" />

      {/* ── Navbar ── */}
      <nav className="landing-nav">
        <Link to="/" className="landing-logo">
          <img src={logo} alt="Shuren" className="h-8 object-contain" />
        </Link>
        <div className="landing-nav-actions">
          <Link to="/login" className="ds-btn-ghost">Sign in</Link>
          <Link to="/register" className="ds-btn-primary">Get Started</Link>
        </div>
      </nav>

      {/* ━━━━━ HERO ━━━━━ */}
      <section className="landing-hero">
        <Reveal>
          <div className="ds-badge">
            <span className="ds-badge-dot" />
            AI-Powered Fitness Coaching
          </div>
        </Reveal>

        <Reveal delay={80}>
          <h1 className="ds-heading-xl landing-h1">
            Your Personal Trainer,
            <br />
            <span className="ds-gradient-text">Nutritionist & Coach</span>
            <br />
            — Powered by AI
          </h1>
        </Reveal>

        <Reveal delay={160}>
          <p className="landing-hero-sub">
            Shuren creates personalized workout plans, meal charts, and real-time
            coaching that adapts to your life. No judgment, no pressure — just
            intelligent&nbsp;support.
          </p>
        </Reveal>

        <Reveal delay={240}>
          <div className="landing-hero-ctas">
            <Link to="/register" id="hero-cta-register" className="ds-btn-primary ds-btn-primary--lg">
              Start Free
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
            </Link>
            <Link to="/login" id="hero-cta-login" className="ds-btn-link">
              Already a member? <span className="underline underline-offset-4">Sign&nbsp;in</span>
            </Link>
          </div>
        </Reveal>

        {/* Stats strip */}
        <Reveal delay={320}>
          <div className="landing-stats">
            {STATS.map((s) => (
              <div key={s.label} className="landing-stat">
                <span className="landing-stat-value ds-gradient-text">{s.value}</span>
                <span className="landing-stat-label">{s.label}</span>
              </div>
            ))}
          </div>
        </Reveal>
      </section>

      {/* ━━━━━ FEATURES ━━━━━ */}
      <section className="landing-features">
        <Reveal>
          <h2 className="ds-heading-lg">
            Meet Your <span className="ds-gradient-text">AI Team</span>
          </h2>
          <p className="ds-section-sub">
            Six specialized agents — each an expert in their domain — collaborating
            to power your fitness journey.
          </p>
        </Reveal>

        <div className="landing-grid">
          {FEATURES.map((f, i) => (
            <Reveal key={f.title} delay={i * 70}>
              <div className="ds-card">
                <div className="ds-icon-box landing-card-icon">{f.icon}</div>
                <h3 className="ds-heading-sm">{f.title}</h3>
                <p className="ds-body-text">{f.description}</p>
                <div className="ds-card-glow" />
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ━━━━━ FINAL CTA ━━━━━ */}
      <section className="landing-final">
        <Reveal>
          <div className="ds-glass-panel">
            <h2 className="ds-heading-lg">
              Ready to Meet Your <span className="ds-gradient-text">AI Fitness&nbsp;Coach</span>?
            </h2>
            <p className="ds-section-sub" style={{ maxWidth: '32rem' }}>
              Join Shuren and get a personalized plan built around your goals,
              schedule, and lifestyle — completely free.
            </p>
            <Link to="/register" id="final-cta-register" className="ds-btn-primary ds-btn-primary--lg">
              Start Your Fitness Journey
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
            </Link>
          </div>
        </Reveal>
      </section>

      {/* ── Footer ── */}
      <footer className="landing-footer">
        © {new Date().getFullYear()} Shuren. All rights reserved.
      </footer>
    </div>
  );
};
