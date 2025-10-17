import React from 'react';
import { Link } from 'react-router-dom';
import './LandingPage.css';

const LandingPage = () => {
  return (
    <div className="landing-page">
      {/* Header */}
      <header className="landing-header">
        <nav className="landing-container">
          <div className="logo">Certaro</div>
          <div className="nav-links">
            <a href="#features">Features</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#benefits">Benefits</a>
            <Link to="/login" className="btn-primary">Sign In</Link>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="hero">
        <div className="landing-container">
          <div className="hero-content">
            <div className="hero-text fade-in">
              <h1>Confidence in Compliance</h1>
              <p>Certaro automatically monitors your internal quality and regulatory documentation against the latest FDA, ISO, and global standards. When regulations change, we instantly detect misalignments and tell you exactly what needs updating.</p>
              <p style={{ fontWeight: 600, color: 'var(--primary)' }}>No manual audits. No missed updates. No surprise findings.</p>
              <Link to="/login" className="btn-primary">Get Started Now</Link>
            </div>
            <div className="hero-visual">
              <div className="compliance-monitor">
                <div className="monitor-header">
                  <span className="status-indicator"></span>
                  <span style={{ fontWeight: 700, color: 'var(--dark)' }}>Live Compliance Monitor</span>
                </div>
                <div className="monitor-item">
                  <span className="label">FDA 21 CFR Part 820</span>
                  <span className="badge badge-compliant">Aligned</span>
                </div>
                <div className="monitor-item">
                  <span className="label">ISO 13485:2016</span>
                  <span className="badge badge-compliant">Aligned</span>
                </div>
                <div className="monitor-item">
                  <span className="label">MDR 2017/745</span>
                  <span className="badge badge-warning">3 Updates</span>
                </div>
                <div className="monitor-item">
                  <span className="label">ISO 14971:2019</span>
                  <span className="badge badge-compliant">Aligned</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features">
        <div className="landing-container">
          <div className="section-header">
            <h2>Continuous Compliance Intelligence</h2>
            <p>Transform your quality management system with automated regulatory monitoring and instant gap detection.</p>
          </div>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🔍</div>
              <h3>Real-Time Monitoring</h3>
              <p>Continuously scan FDA, ISO, MDR, and global regulatory updates as they're published. Never miss a critical change.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">⚡</div>
              <h3>Instant Gap Detection</h3>
              <p>AI-powered engine identifies affected sections, documents, and processes the moment regulations change.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3>Actionable Reports</h3>
              <p>Receive detailed impact maps showing exactly where each update touches your systems and what needs fixing.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔒</div>
              <h3>Secure Analysis</h3>
              <p>Encrypted, on-premise options available. Your sensitive documentation never leaves your control.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📈</div>
              <h3>Audit Trail</h3>
              <p>Maintain complete traceability with documented change history and compliance lineage.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🌍</div>
              <h3>Global Coverage</h3>
              <p>Monitor regulations across all major markets - FDA, EU MDR, Health Canada, MHLW, and more.</p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="how-it-works">
        <div className="landing-container">
          <div className="section-header">
            <h2>How It Works</h2>
            <p>From upload to audit-ready in four simple steps</p>
          </div>
          <div className="steps">
            <div className="step">
              <div className="step-number">1</div>
              <h3>Upload or Connect</h3>
              <p>Integrate your existing document repository or upload files directly.</p>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <h3>Compare and Analyze</h3>
              <p>Certaro continuously scans for new or updated regulations from FDA, ISO, MDR, and other authorities.</p>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <h3>Gap Detection</h3>
              <p>Our engine identifies affected sections, documents, and processes — highlighting what must change.</p>
            </div>
            <div className="step">
              <div className="step-number">4</div>
              <h3>Actionable Reports</h3>
              <p>Receive detailed impact maps showing where each regulatory update touches your internal systems.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section id="benefits" className="benefits">
        <div className="landing-container">
          <div className="section-header">
            <h2>Why It Matters</h2>
            <p>Transform compliance from a burden to a competitive advantage</p>
          </div>
          <div className="benefits-grid">
            <div className="benefit">
              <div className="benefit-icon">✓</div>
              <div className="benefit-content">
                <h4>Stay audit-ready, every day</h4>
                <p>No last-minute scrambles when standards change. Be confident in every inspection.</p>
              </div>
            </div>
            <div className="benefit">
              <div className="benefit-icon">⏱</div>
              <div className="benefit-content">
                <h4>Cut review cycles</h4>
                <p>Automate what used to take teams weeks. Focus on improvement, not paperwork.</p>
              </div>
            </div>
            <div className="benefit">
              <div className="benefit-icon">🎯</div>
              <div className="benefit-content">
                <h4>Prevent compliance drift</h4>
                <p>Maintain alignment as regulations evolve. Never fall behind on critical updates.</p>
              </div>
            </div>
            <div className="benefit">
              <div className="benefit-icon">💰</div>
              <div className="benefit-content">
                <h4>Protect revenue</h4>
                <p>Avoid noncompliance penalties, shipment holds, and certification lapses.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Industries */}
      <section className="industries">
        <div className="landing-container">
          <div className="section-header">
            <h2>Built for Regulated Industries</h2>
          </div>
          <div className="industry-content">
            <p>Today, Certaro serves medical device manufacturers and suppliers who need to stay current with evolving FDA and ISO requirements. Our technology extends easily to pharma, biotech, and aerospace — anywhere quality systems must align with external standards.</p>
            <div className="industry-tags">
              <span className="industry-tag">Medical Devices</span>
              <span className="industry-tag">Pharmaceuticals</span>
              <span className="industry-tag">Biotechnology</span>
              <span className="industry-tag">Aerospace</span>
              <span className="industry-tag">Automotive</span>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section id="demo" className="cta">
        <div className="landing-container">
          <h2>See where your QMS stands today</h2>
          <p>Get started with Certaro and ensure continuous compliance.</p>
          <Link to="/login" className="btn-white">Get Started</Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="landing-container">
          <p>&copy; 2025 Certaro.io - Confidence in Compliance</p>
          <p>Automated Regulatory Monitoring for Quality Management Systems</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
