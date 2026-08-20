import * as React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { 
  Home, 
  BarChart2, 
  Terminal, 
  Beaker, 
  Menu, 
  X, 
  Search, 
  Sparkles, 
  User, 
  BookOpen,
  FolderDot
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useProjectStore } from "../store/projectStore";
import { StatusIndicator } from "../components/StatusIndicator";
import { Button } from "../components/Button";
import { useAuth } from "../hooks/useAuth";
import { useWorkspaces } from "../hooks/useWorkspaces";
import { useProjects, useProject } from "../hooks/useProjects";

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const { 
    selectedWorkspaceId, 
    setSelectedWorkspaceId, 
    selectedProjectId, 
    setSelectedProjectId, 
    learnMode, 
    toggleLearnMode 
  } = useProjectStore();
  const { user, logoutMutation } = useAuth();
  const { workspaces } = useWorkspaces();
  const { projects } = useProjects(selectedWorkspaceId);
  const { project: activeProject } = useProject(selectedProjectId);

  const [isSidebarOpen, setIsSidebarOpen] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState("");
  const [showSearchModal, setShowSearchModal] = React.useState(false);
  const [showCreateProjectModal, setShowCreateProjectModal] = React.useState(false);
  const [newProjectName, setNewProjectName] = React.useState("");
  const [newProjectPath, setNewProjectPath] = React.useState("");
  const { createProjectMutation } = useProjects(selectedWorkspaceId);

  const navigate = useNavigate();
  const location = useLocation();

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName) return;
    
    // Default path if empty
    const resolvedPath = newProjectPath || `./playground/project_${newProjectName.toLowerCase().replace(/\s+/g, '_')}`;

    try {
      const created = await createProjectMutation.mutateAsync({
        projectName: newProjectName,
        projectPath: resolvedPath,
      });
      setSelectedProjectId(created.id);
      setShowCreateProjectModal(false);
      setNewProjectName("");
      setNewProjectPath("");
    } catch (err: any) {
      alert(err.message || "Failed to create project");
    }
  };

  React.useEffect(() => {
    if (selectedWorkspaceId === null && workspaces.length > 0) {
      setSelectedWorkspaceId(workspaces[0].id);
    }
  }, [workspaces, selectedWorkspaceId, setSelectedWorkspaceId]);

  React.useEffect(() => {
    if (selectedProjectId === null && projects.length > 0) {
      setSelectedProjectId(projects[0].id);
    }
  }, [projects, selectedProjectId, setSelectedProjectId]);

  const navItems = [
    { id: "dashboard", label: "Dashboard", path: "/workspace", icon: <Home className="h-4 w-4" /> },
    { id: "analyze", label: "Analyze Dataset", path: "/workspace/analyze", icon: <BarChart2 className="h-4 w-4" /> },
    { id: "run", label: "Run Pipeline", path: "/workspace/run", icon: <Terminal className="h-4 w-4" /> },
    { id: "experiments", label: "Experiments", path: "/workspace/experiments", icon: <Beaker className="h-4 w-4" /> },
  ];

  const handleNavClick = (path: string) => {
    navigate(path);
    setIsSidebarOpen(false);
  };

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setShowSearchModal((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col md:flex-row">
      {/* Mobile Top Bar */}
      <header className="md:hidden flex h-14 items-center justify-between border-b border-border bg-card px-4 sticky top-0 z-30">
        <div className="flex items-center space-x-2">
          <FolderDot className="h-5 w-5 text-primary" />
          <span className="font-bold tracking-tight text-sm">ML-OS</span>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={() => setShowSearchModal(true)}
            aria-label="Search command palette"
          >
            <Search className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={() => setIsSidebarOpen(true)}
            aria-label="Open sidebar navigation"
          >
            <Menu className="h-5 w-5" />
          </Button>
        </div>
      </header>

      {/* Sidebar Navigation */}
      <aside
            className={`fixed inset-y-0 left-0 z-40 w-64 border-r border-border bg-card/95 backdrop-blur-sm p-4 flex flex-col justify-between transform transition-transform duration-250 ease-in-out md:translate-x-0 md:static md:z-auto md:bg-card md:flex md:w-60 md:h-screen ${
              isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
            }`}
          >
            <div className="space-y-6">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="p-1 rounded bg-primary/10 border border-primary/20">
                    <FolderDot className="h-5 w-5 text-primary" />
                  </span>
                  <span className="font-bold tracking-tight text-base">
                    ML<span className="text-primary font-mono font-normal">-OS</span>
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="md:hidden h-8 w-8 p-0"
                  onClick={() => setIsSidebarOpen(false)}
                  aria-label="Close sidebar navigation"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {/* Project Title Info */}
              <div className="p-3 rounded border border-border bg-background/50 text-left space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">
                    Project Workspace
                  </span>
                  <button
                    onClick={() => {
                      setNewProjectName("");
                      setNewProjectPath("");
                      setShowCreateProjectModal(true);
                    }}
                    className="text-[10px] text-primary hover:underline font-mono"
                  >
                    + New
                  </button>
                </div>
                {projects.length > 0 ? (
                  <select
                    value={selectedProjectId || ""}
                    onChange={(e) => {
                      const id = parseInt(e.target.value, 10);
                      setSelectedProjectId(isNaN(id) ? null : id);
                    }}
                    className="w-full bg-card border border-border rounded text-xs font-semibold text-foreground p-1 focus:outline-none focus:border-primary"
                  >
                    <option value="">Select Project...</option>
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.project_name}
                      </option>
                    ))}
                  </select>
                ) : (
                  <span className="text-xs font-semibold text-muted-foreground block">
                    No Projects Found
                  </span>
                )}
              </div>

              {/* Navigation Options */}
              <nav className="flex flex-col space-y-1">
                <span className="text-[9px] font-mono font-bold text-muted-foreground/60 uppercase tracking-wider px-2 mb-2 block text-left">
                  Automated Loop
                </span>
                {navItems.map((item) => {
                  const isActive = location.pathname === item.path;
                  return (
                    <button
                      key={item.id}
                      onClick={() => handleNavClick(item.path)}
                      className={`flex items-center space-x-3 px-3 py-2 text-xs font-medium rounded transition-all focus-visible:outline-none focus-visible:text-primary ${
                        isActive
                          ? "bg-secondary text-primary font-semibold border-l-2 border-primary"
                          : "text-muted-foreground hover:bg-secondary/40 hover:text-foreground"
                      }`}
                    >
                      {item.icon}
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </nav>
            </div>

            {/* Bottom Config Panels */}
            <div className="space-y-4 pt-4 border-t border-border/60">
              {/* Learn Mode Toggle */}
              <div className="flex items-center justify-between px-2 bg-secondary/30 py-2 rounded border border-border/10">
                <div className="flex items-center space-x-2 text-left">
                  <BookOpen className="h-3.5 w-3.5 text-primary" />
                  <span className="text-[11px] font-medium text-foreground">Learn Mode</span>
                </div>
                <label className="relative inline-flex items-center cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={learnMode}
                    onChange={toggleLearnMode}
                    className="sr-only peer"
                    aria-label="Toggle Learn Mode educational tips"
                  />
                  <div className="w-7 h-4 bg-secondary border border-border/80 rounded-full peer peer-focus:ring-0 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[3px] after:left-[3px] after:bg-muted-foreground after:border-border after:border after:rounded-full after:h-2.5 after:w-2.5 after:transition-all peer-checked:bg-primary peer-checked:after:bg-primary-foreground peer-checked:after:border-transparent"></div>
                </label>
              </div>

              {/* Status */}
              <div className="flex items-center justify-between px-2 text-xs">
                <span className="text-muted-foreground font-mono text-[10px]">Kernel Status</span>
                <StatusIndicator status="success" label="Online" />
              </div>

              {/* User Profiling Panel */}
              <div className="flex items-center justify-between border-t border-border/40 pt-3">
                <div className="flex items-center space-x-2.5 min-w-0">
                  <div className="h-7 w-7 rounded-full bg-secondary border border-border flex items-center justify-center text-xs">
                    <User className="h-3.5 w-3.5 text-muted-foreground" />
                  </div>
                  <div className="text-left min-w-0">
                    <p className="text-[11px] font-semibold text-foreground leading-none truncate">
                      {user?.email || "ML Engineer"}
                    </p>
                    <p className="text-[9px] font-mono text-muted-foreground leading-none mt-0.5 truncate">
                      Active Session
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-[10px] hover:bg-secondary"
                  disabled={logoutMutation.isPending}
                  onClick={async () => {
                    await logoutMutation.mutateAsync();
                    navigate("/login");
                  }}
                >
                  {logoutMutation.isPending ? "Logging out..." : "Exit"}
                </Button>
              </div>
            </div>
          </aside>

      {/* Main Panel Content Frame */}
      <div className="flex-1 flex flex-col md:h-screen overflow-hidden">
        {/* Top Header desktop search / info */}
        <header className="hidden md:flex h-14 items-center justify-between border-b border-border bg-card/30 px-6 select-none shrink-0">
          <div className="flex items-center space-x-4">
            <span className="text-xs font-mono text-muted-foreground">
              Workspace path: <strong className="text-foreground">{activeProject?.project_path || "C:/Users/.../ml-os"}</strong>
            </span>
          </div>

          <div className="flex items-center space-x-4">
            {/* Search command bar shortcut */}
            <Button
              variant="outline"
              size="sm"
              className="text-muted-foreground hover:text-foreground h-8 px-3 flex items-center space-x-3 bg-secondary/20 border-border/80"
              onClick={() => setShowSearchModal(true)}
            >
              <span className="flex items-center text-[11px]">
                <Search className="h-3.5 w-3.5 mr-2" />
                Quick Search
              </span>
              <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded bg-secondary px-1.5 font-mono text-[9px] font-medium text-muted-foreground border border-border">
                <span>Ctrl</span>K
              </kbd>
            </Button>
            
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0 hover:bg-secondary">
              <Sparkles className="h-4 w-4 text-primary" />
            </Button>
          </div>
        </header>

        {/* Scrollable View Content wrapper */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 bg-background">
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.15 }}
            className="h-full flex flex-col space-y-6"
          >
            {children}
          </motion.div>
        </main>
      </div>

      {/* Command Palette Modal */}
      <AnimatePresence>
        {showSearchModal && (
          <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowSearchModal(false)}
              className="absolute inset-0 bg-background/85 backdrop-blur-sm"
            />
            
            <motion.div
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.97 }}
              transition={{ duration: 0.1 }}
              className="relative z-10 w-full max-w-lg rounded border border-border bg-card shadow-2xl overflow-hidden focus:outline-none"
            >
              <div className="flex items-center px-4 border-b border-border">
                <Search className="h-4 w-4 text-muted-foreground mr-3" />
                <input
                  type="text"
                  placeholder="Type a command or search project files..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="h-11 w-full bg-transparent text-sm placeholder:text-muted-foreground focus-visible:outline-none"
                  autoFocus
                />
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 px-1.5 text-[9px] font-mono border border-border bg-secondary"
                  onClick={() => setShowSearchModal(false)}
                >
                  ESC
                </Button>
              </div>

              {/* Commands List */}
              <div className="p-2 max-h-60 overflow-y-auto text-left">
                <div className="px-2 py-1.5 text-[10px] font-mono font-bold text-muted-foreground/60 uppercase">
                  Commands
                </div>
                <button
                  onClick={() => { handleNavClick("/workspace"); setShowSearchModal(false); }}
                  className="w-full text-left px-3 py-2 text-xs hover:bg-secondary rounded flex items-center space-x-2"
                >
                  <Home className="h-3.5 w-3.5" />
                  <span>Go to Dashboard Overview</span>
                </button>
                <button
                  onClick={() => { handleNavClick("/workspace/analyze"); setShowSearchModal(false); }}
                  className="w-full text-left px-3 py-2 text-xs hover:bg-secondary rounded flex items-center space-x-2"
                >
                  <BarChart2 className="h-3.5 w-3.5" />
                  <span>Configure and Analyze Dataset</span>
                </button>
                <button
                  onClick={() => { handleNavClick("/workspace/run"); setShowSearchModal(false); }}
                  className="w-full text-left px-3 py-2 text-xs hover:bg-secondary rounded flex items-center space-x-2"
                >
                  <Terminal className="h-3.5 w-3.5" />
                  <span>Trigger AutoML Pipeline Run</span>
                </button>
                <button
                  onClick={() => { handleNavClick("/workspace/experiments"); setShowSearchModal(false); }}
                  className="w-full text-left px-3 py-2 text-xs hover:bg-secondary rounded flex items-center space-x-2"
                >
                  <Beaker className="h-3.5 w-3.5" />
                  <span>Compare Run Experiments</span>
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Create Project Modal */}
      <AnimatePresence>
        {showCreateProjectModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowCreateProjectModal(false)}
              className="absolute inset-0 bg-background/85 backdrop-blur-sm"
            />
            
            <motion.div
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.97 }}
              transition={{ duration: 0.15 }}
              className="relative z-10 w-full max-w-sm rounded border border-border bg-card shadow-2xl p-6 text-left"
            >
              <h2 className="text-sm font-semibold tracking-tight text-foreground mb-4">
                Create New ML Project
              </h2>
              
              <form onSubmit={handleCreateProject} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-mono text-muted-foreground block">
                    Project Name
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Titanic Classification"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    className="w-full bg-background border border-border rounded text-xs px-3 py-2 text-foreground focus-visible:outline-none focus-visible:border-primary"
                  />
                </div>
                
                <div className="space-y-1.5">
                  <label className="text-[10px] font-mono text-muted-foreground block">
                    Project Path (Absolute or Workspace Relative)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. playground/titanic (Leave blank for default)"
                    value={newProjectPath}
                    onChange={(e) => setNewProjectPath(e.target.value)}
                    className="w-full bg-background border border-border rounded text-xs px-3 py-2 text-foreground focus-visible:outline-none focus-visible:border-primary"
                  />
                </div>
                
                <div className="flex justify-end space-x-2 pt-2">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="text-xs"
                    onClick={() => setShowCreateProjectModal(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="primary"
                    size="sm"
                    className="text-xs"
                    disabled={createProjectMutation.isPending}
                  >
                    {createProjectMutation.isPending ? "Creating..." : "Create"}
                  </Button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
