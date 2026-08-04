"""
CyberGuard Enterprise SOC UI Styling & Glassmorphic Dashboard Components
"""
import streamlit as st

APP_LOGO_SVG = """
<svg width="36" height="36" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle;">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="url(#brand-shield-grad)" stroke="#0284c7" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M12 8v4m0 3.5h.01" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round"/>
    <defs>
        <linearGradient id="brand-shield-grad" x1="4" y1="2" x2="20" y2="22" gradientUnits="userSpaceOnUse">
            <stop stop-color="#0284c7"/>
            <stop offset="1" stop-color="#6366f1"/>
        </linearGradient>
    </defs>
</svg>
"""

SVG_ICONS = {
    "overview": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>',
    "incidents": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "anomalies": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="15" x2="23" y2="15"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="15" x2="4" y2="15"/></svg>',
    "geo": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    "profiles": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    "sql": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
    "stats": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "chart_line": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "chart_pie": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>',
    "users": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-3-3.87"/><path d="M9 21v-2a4 4 0 0 1 3-3.87"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "device": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',
    "search": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "export": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
    "zap": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "target": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    "plane": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.8 19.2L16 11l3.5-3.5C21 6 21.5 4 21 3.5c-.5-.5-2.5 0-4 1.5L13.5 8.5 5.3 6.7c-.6-.1-1.1.1-1.4.6l-.6.9 4.3 3.3-3 3-2.1-.7c-.3-.1-.7 0-.9.3l-.4.5 2.7 2.7 2.7 2.7.5-.4c.3-.2.4-.6.3-.9l-.7-2.1 3-3 3.3 4.3.9-.6c.5-.3.7-.8.6-1.4z"/></svg>',
}

def get_svg_icon(name: str, size: int = 22, color: str = "#0284c7") -> str:
    """Return inline SVG icon string."""
    template = SVG_ICONS.get(name, SVG_ICONS["overview"])
    return template.format(size=size, color=color)

def render_section_title(title_text: str, icon_name: str = "overview"):
    """Render crisp section title with SVG icon."""
    icon_html = get_svg_icon(icon_name, size=24, color="#0284c7")
    html_content = f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">{icon_html}<h3 style="margin: 0; font-size: 1.35rem; font-weight: 700;">{title_text}</h3></div>'
    st.markdown(html_content, unsafe_allow_html=True)

def apply_soc_theme():
    """Apply CrowdStrike / Sentinel inspired responsive glassmorphic styling supporting Light & Dark themes."""
    st.markdown("""
<style>
/* Base typography & layout */
.stApp {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* Metric Glass Card Styling - Adaptive Theme */
div[data-testid="stMetric"] {
    background-color: var(--secondary-background-color) !important;
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    border-color: rgba(56, 189, 248, 0.6);
}
div[data-testid="stMetricValue"] {
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    color: #0284c7 !important;
    font-size: 1.8rem;
}
div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] p,
div[data-testid="stMetricLabel"] label,
div[data-testid="stMetricLabel"] span,
div[data-testid="stMetricLabel"] div {
    color: var(--text-color) !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-size: 0.75rem;
    opacity: 0.85 !important;
}

/* Headings */
h1, h2, h3 {
    font-family: 'Outfit', sans-serif;
    letter-spacing: -0.5px;
}

.soc-header {
    background: linear-gradient(90deg, #0284c7 0%, #6366f1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
}

/* Status Badge CSS */
.badge-critical {
    background-color: #7f1d1d;
    color: #fca5a5;
    padding: 4px 8px;
    border-radius: 6px;
    font-weight: 600;
}
.badge-high {
    background-color: #991b1b;
    color: #fecaca;
    padding: 4px 8px;
    border-radius: 6px;
    font-weight: 600;
}
.badge-medium {
    background-color: #854d0e;
    color: #fef08a;
    padding: 4px 8px;
    border-radius: 6px;
    font-weight: 600;
}
.badge-low {
    background-color: #14532d;
    color: #bbf7d0;
    padding: 4px 8px;
    border-radius: 6px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

def render_header():
    """Render top enterprise brand header using SVG logo."""
    header_html = f"""<div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 0px; border-bottom: 1px solid rgba(148, 163, 184, 0.2); margin-bottom: 20px;">
<div style="display: flex; align-items: center; gap: 14px;">
{APP_LOGO_SVG}
<div>
<h1 class="soc-header" style="margin: 0; font-size: 2.1rem; line-height: 1.2;">CYBERGUARD SOC ENTERPRISE</h1>
<p style="opacity: 0.8; margin: 4px 0 0 0; font-size: 0.92rem;">Real-Time AI Authentication Behavioral Threat Analytics & Risk Engine</p>
</div>
</div>
<div style="text-align: right;">
<span style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid #10b981; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">LIVE MONITORING</span>
</div>
</div>"""
    st.markdown(header_html, unsafe_allow_html=True)



