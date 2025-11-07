### 👋 Hi, I'm Carl Shipley

I'm a Principal Technical Program Manager driving Azure Fundamentals across a portfolio of cloud services. While my day job centers on strategy and program delivery, I actively code and develop solutions.

**Full-Stack Dashboard Development:**
- Python HTTP servers with dynamic query execution and real-time data visualization
- Interactive HTML/JavaScript dashboards with advanced filtering, sorting, and export capabilities
- Pluggable JSON configuration frameworks that enable rapid deployment of new monitoring scenarios
- Dynamic query loading systems that read configurations from file-based storage

**Advanced Data Engineering:**
- Complex Kusto (KQL) query development for multi-service risk analysis and operational insights
- Automated exception handling workflows that streamline compliance and remediation tracking
- JSON-based query templating systems that scale across diverse service portfolios
- Data transformation and HTML table generation for actionable business intelligence

**DevOps & Development Tools:**
- Git-based workflow management with branch strategies for dashboard releases
- AI-assisted development using GitHub Copilot for accelerated coding and debugging
- Batch automation scripts for one-click environment setup and dashboard deployment
- VS Code integration for enhanced development productivity

🔗 [Connect with me on LinkedIn](https://www.linkedin.com/in/carlkshipley/) for my professional story.


# Technical Development Examples

Real examples from my coding projects demonstrating full-stack development capabilities.

## Full-Stack Dashboard Development

### 🐍 Python HTTP Servers with Dynamic Query Execution
- **`DashboardRequestHandler` class** in `server.py` with routes like `/api/data/project_alpha` that execute Kusto queries dynamically
- **Server handles GET requests** to `/api/queries` to list available configurations
- **Dynamic routing** for real-time data processing and API endpoints

### 🌐 Interactive HTML/JavaScript Dashboards with Export Capabilities
- **`dashboard.html`** has `exportTable()` function supporting CSV, Excel, PDF, Word formats
- **`extractTableData()` and `downloadFile()`** methods for data export functionality
- **Real filtering and sorting** functionality in the web interface
- **Multi-format export system** for business intelligence reporting

### ⚙️ Pluggable JSON Configuration Frameworks
- **15 different `.json` files** in `/queries/` folder (`service_monitoring.json`, `compliance_tracking.json`, etc.)
- **Each JSON defines** `displayName`, `query`, and `columns` for dynamic loading
- **Modular architecture** enabling rapid deployment of new monitoring scenarios

---

## Advanced Data Engineering

### 📊 Complex Kusto (KQL) Query Development
- **Real example** from `service_monitoring.json`: Multi-table joins across incident tracking tables with dynamic parameter filtering
- **Dynamic filtering pattern**: `where isempty(ServiceGroup_param) or ServiceGroupName in (ServiceGroup_param)` for optional filtering
- **Production-grade queries** handling large datasets and complex business logic

### 🔧 JSON-Based Query Templating Systems
- **Standardized structure**: Each query file has `displayName`, `query`, `columns` properties
- **Scalable architecture**: System scales across 15 different monitoring scenarios
- **Projects include**: Service Health, Compliance Tracking, Risk Assessment, Performance Analytics, Security Monitoring, Operational Insights

---

## DevOps & Development Tools

### 🚀 Batch Automation Scripts
- **`Dashboard-Launcher.bat`** with error checking, Python validation, and auto-browser opening
- **Real path validation** and environment setup automation
- **One-click deployment** with comprehensive error handling and user feedback

### 🔀 Git-Based Workflow Management
- **Active branches**: `master`, `dashboard-improvements`, `backup-working-state`, `feature/analytics-dashboard`
- **Commit history** showing incremental feature development and version control
- **Branch strategies** for production releases and feature development

---

## Key Technologies Used

| Category | Technologies |
|----------|-------------|
| **Backend** | Python, HTTP servers, JSON APIs |
| **Frontend** | HTML5, JavaScript, CSS, Interactive dashboards |
| **Data** | Kusto (KQL), JSON templating, Dynamic queries |
| **DevOps** | Git, Batch scripting, Automation tools |
| **Export** | CSV, Excel, PDF, Word generation |

---

*These are all concrete examples from actual production codebases, demonstrating real-world application of full-stack development skills.*
