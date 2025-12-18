# Phase 107: Styling

## Objective

Implement comprehensive CSS styling for all frontend components.

## Prerequisites

- Phase 106 completed
- All components ready for styling

## Steps

### 1.1: Create Global Styles (src/styles/style.css)

Create `frontend/src/styles/style.css`:

```css
/* Reset */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f5f5f5;
  color: #333;
}

/* Loading */
.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  font-size: 18px;
  color: #666;
}

/* Login Page */
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-container {
  width: 100%;
  max-width: 400px;
  padding: 20px;
}

.login-form {
  background: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.login-form h1 {
  margin-bottom: 8px;
  text-align: center;
  color: #333;
  font-size: 28px;
}

.login-form .subtitle {
  text-align: center;
  color: #999;
  margin-bottom: 30px;
  font-size: 14px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #333;
  font-weight: 500;
  font-size: 14px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.login-form button {
  width: 100%;
  padding: 12px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s;
}

.login-form button:hover:not(:disabled) {
  background: #5568d3;
}

.login-form button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  padding: 12px;
  margin-bottom: 20px;
  background: #fee;
  color: #c33;
  border-radius: 4px;
  font-size: 14px;
  border-left: 4px solid #c33;
}

/* Pages */
.page {
  min-height: 100vh;
  background-color: #f5f5f5;
}

/* Header */
.header {
  background: white;
  border-bottom: 1px solid #ddd;
  padding: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 40px;
}

.header .logo h1 {
  font-size: 24px;
  color: #333;
  margin: 0;
}

.nav-menu {
  display: flex;
  gap: 30px;
  flex: 1;
}

.nav-menu a {
  color: #666;
  text-decoration: none;
  font-size: 15px;
  transition: color 0.3s;
}

.nav-menu a:hover {
  color: #667eea;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

.username {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.btn-logout {
  padding: 8px 16px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.btn-logout:hover {
  background: #e0e0e0;
}

.main-content {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 20px;
}

/* Breadcrumbs */
.breadcrumbs {
  max-width: 1200px;
  margin: 0 auto;
  padding: 12px 20px;
  font-size: 13px;
  color: #666;
  background: white;
  border-bottom: 1px solid #eee;
}

.breadcrumbs a {
  color: #667eea;
  text-decoration: none;
  transition: color 0.3s;
}

.breadcrumbs a:hover {
  color: #5568d3;
  text-decoration: underline;
}

.breadcrumbs .separator {
  margin: 0 8px;
  color: #ddd;
}

.breadcrumbs .current {
  color: #333;
  font-weight: 500;
}

/* Home Page */
.hero {
  background: white;
  padding: 60px 20px;
  border-radius: 8px;
  text-align: center;
  margin-bottom: 30px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.hero h2 {
  font-size: 32px;
  margin-bottom: 10px;
  color: #333;
}

.hero p {
  font-size: 16px;
  color: #999;
}

.dashboard-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  padding: 30px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.stat-number {
  font-size: 40px;
  font-weight: bold;
  color: #667eea;
  margin-bottom: 10px;
}

.stat-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.quick-actions {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.quick-actions h3 {
  margin-bottom: 20px;
  color: #333;
}

.action-buttons {
  display: flex;
  gap: 15px;
}

.action-buttons a {
  padding: 12px 24px;
  border-radius: 4px;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s;
}

/* Buttons */
.btn-primary {
  background: #667eea;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: background 0.3s;
}

.btn-primary:hover {
  background: #5568d3;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
  border: 1px solid #ddd;
  padding: 10px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: background 0.3s;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-success {
  background: #10b981;
  color: white;
}

.btn-success:hover {
  background: #059669;
}

.btn-warning {
  background: #f59e0b;
  color: white;
}

.btn-warning:hover {
  background: #d97706;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
}

.btn-info {
  background: #3b82f6;
  color: white;
}

.btn-info:hover {
  background: #2563eb;
}

/* Forms */
.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.server-form {
  background: white;
  padding: 30px;
  border-radius: 8px;
  margin-bottom: 30px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.server-form h3 {
  margin-bottom: 30px;
  color: #333;
  border-bottom: 2px solid #667eea;
  padding-bottom: 15px;
}

.form-section {
  margin-bottom: 30px;
  padding-bottom: 30px;
  border-bottom: 1px solid #eee;
}

.form-section:last-of-type {
  border-bottom: none;
}

.form-section legend {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
  display: block;
}

.form-group label {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  color: #333;
  font-weight: 500;
  font-size: 14px;
}

.form-group input[type="checkbox"] {
  margin-right: 8px;
  width: auto;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-group small {
  display: block;
  margin-top: 4px;
  color: #999;
  font-size: 12px;
}

.input-with-button {
  display: flex;
  gap: 10px;
}

.input-with-button input {
  flex: 1;
}

.tools-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 15px;
}

.tool-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 13px;
  color: #333;
}

.tool-badge .btn-remove {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 18px;
  padding: 0;
  margin-left: 4px;
  transition: color 0.3s;
}

.tool-badge .btn-remove:hover {
  color: #c33;
}

.env-vars-editor {
  display: grid;
  grid-template-columns: 1fr;
  gap: 15px;
}

.env-var-item {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 10px;
  align-items: end;
}

.env-key,
.env-value {
  padding: 10px !important;
  font-size: 13px !important;
}

.env-var-item .btn-remove {
  padding: 8px 12px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.3s;
}

.env-var-item .btn-remove:hover {
  background: #dc2626;
}

/* Sections */
.servers-container,
.processes-container {
  background: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.section-header h2 {
  margin: 0;
  color: #333;
  font-size: 20px;
}

.section-header .subtitle {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.info-box {
  background: #f0f9ff;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 20px;
  margin-top: 30px;
}

.info-box h4 {
  margin: 0 0 15px 0;
  color: #0c4a6e;
  font-size: 14px;
}

.info-box ol {
  margin: 0;
  padding-left: 20px;
  color: #0c4a6e;
  font-size: 13px;
  line-height: 1.6;
}

.info-box li {
  margin-bottom: 8px;
}

.poll-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.poll-select {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
}

/* Log Viewer Modal */
.log-viewer-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  z-index: 1000;
}

.log-viewer-header {
  background: #333;
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #222;
}

.log-viewer-header h3 {
  margin: 0;
  font-size: 18px;
}

.log-controls {
  display: flex;
  gap: 15px;
  align-items: center;
}

.log-type-select {
  padding: 6px 10px;
  border: 1px solid #555;
  border-radius: 4px;
  background: #444;
  color: white;
  font-size: 13px;
  cursor: pointer;
}

.btn-close {
  background: none;
  border: none;
  color: white;
  font-size: 32px;
  cursor: pointer;
  padding: 0;
  margin: 0;
  line-height: 1;
  transition: color 0.3s;
}

.btn-close:hover {
  color: #ff6b6b;
}

.log-viewer-content {
  flex: 1;
  background: #1e1e1e;
  color: #d4d4d4;
  overflow: auto;
  padding: 20px;
}

.log-output {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  color: #d4d4d4;
}

.log-viewer-content p {
  color: #999;
  font-style: italic;
}

/* Tables */
.servers-table,
.processes-table {
  width: 100%;
  border-collapse: collapse;
}

.servers-table thead,
.processes-table thead {
  background: #f9f9f9;
  border-bottom: 2px solid #ddd;
}

.servers-table th,
.processes-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #666;
  font-size: 14px;
}

.servers-table td,
.processes-table td {
  padding: 12px;
  border-bottom: 1px solid #eee;
}

.servers-table tbody tr:hover,
.processes-table tbody tr:hover {
  background: #f9f9f9;
}

.process-name {
  font-weight: 500;
  color: #333;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.status-running {
  background: #d1fae5;
  color: #065f46;
}

.status-stopped {
  background: #fee2e2;
  color: #7f1d1d;
}

.status-fatal {
  background: #fecaca;
  color: #7f1d1d;
}

.status-unknown {
  background: #e5e7eb;
  color: #374151;
}

.actions {
  display: flex;
  gap: 8px;
}

.actions button {
  white-space: nowrap;
}

.form-actions {
  display: flex;
  gap: 15px;
  margin-top: 30px;
}

.form-actions button {
  flex: 1;
}
```

---

## Verification Checklist

- [ ] `frontend/src/styles/style.css` created
- [ ] Global styles load correctly
- [ ] All components styled appropriately
- [ ] Responsive design working
- [ ] Color scheme consistent
- [ ] Animations and transitions smooth
- [ ] Dark mode for log viewer works

## Next Step

Proceed to [108-html-and-build.md](./108-html-and-build.md)
