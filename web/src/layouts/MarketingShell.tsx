import * as React from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { FolderDot, ArrowRight, Menu, X } from "lucide-react";
import { Button } from "../components/Button";

interface MarketingShellProps {
  children: React.ReactNode;
}

export const MarketingShell: React.FC<MarketingShellProps> = ({ children }) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const links = [
    { label: "Features", path: "/features" },
    { label: "How It Works", path: "/how-it-works" },
    { label: "Docs", path: "/docs" },
    { label: "Pricing", path: "/pricing" },
    { label: "About", path: "/about" },
  ];

  const handleNav = (path: string) => {
    navigate(path);
    setIsOpen(false);
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between">
      {/* Header Navigation */}
      <header className="border-b border-border bg-card/20 backdrop-blur-sm sticky top-0 z-30 px-6 h-14 flex items-center justify-between select-none">
        {/* Logo */}
        <Link to="/" className="flex items-center space-x-2">
          <FolderDot className="h-5 w-5 text-primary" />
          <span className="font-bold tracking-tight text-sm">
            ML<span className="text-primary font-mono font-normal">-OS</span>
          </span>
        </Link>

        {/* Desktop Links */}
        <nav className="hidden md:flex items-center space-x-6">
          {links.map((lnk) => {
            const isActive = location.pathname === lnk.path;
            return (
              <Link
                key={lnk.path}
                to={lnk.path}
                className={`text-xs font-medium transition-colors hover:text-foreground ${isActive ? "text-primary font-semibold" : "text-muted-foreground"}`}
              >
                {lnk.label}
              </Link>
            );
          })}
        </nav>

        {/* Desktop CTAs */}
        <div className="hidden md:flex items-center space-x-3">
          <Button
            variant="ghost"
            size="sm"
            className="text-xs h-8 text-muted-foreground hover:text-foreground"
            onClick={() => navigate("/login")}
          >
            Sign In
          </Button>
          <Button
            variant="primary"
            size="sm"
            className="text-xs h-8"
            onClick={() => navigate("/workspace")}
          >
            Start Building
            <ArrowRight className="h-3 w-3 ml-1.5" />
          </Button>
        </div>

        {/* Mobile Toggle */}
        <Button
          variant="ghost"
          size="sm"
          className="md:hidden h-8 w-8 p-0"
          onClick={() => setIsOpen(!isOpen)}
          aria-label="Toggle navigation menu"
        >
          {isOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </Button>
      </header>

      {/* Mobile Menu Panel */}
      {isOpen && (
        <div className="md:hidden fixed top-14 left-0 right-0 bottom-0 bg-background/95 backdrop-blur-sm z-20 flex flex-col p-6 space-y-4 animate-in fade-in slide-in-from-top-4 duration-150 border-b border-border">
          {links.map((lnk) => (
            <button
              key={lnk.path}
              onClick={() => handleNav(lnk.path)}
              className="text-sm font-medium py-2 text-left border-b border-border/40 text-muted-foreground hover:text-foreground"
            >
              {lnk.label}
            </button>
          ))}
          <div className="flex flex-col space-y-2 pt-4">
            <Button
              variant="secondary"
              size="md"
              className="w-full text-xs"
              onClick={() => handleNav("/login")}
            >
              Sign In
            </Button>
            <Button
              variant="primary"
              size="md"
              className="w-full text-xs"
              onClick={() => handleNav("/workspace")}
            >
              Start Building
              <ArrowRight className="h-3 w-3 ml-1.5" />
            </Button>
          </div>
        </div>
      )}

      {/* Main Contents */}
      <main className="flex-1 w-full">{children}</main>

      {/* Footer */}
      <footer className="border-t border-border bg-card/10 py-8 px-6 text-center select-none">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <FolderDot className="h-4 w-4 text-primary" />
            <span className="text-xs font-semibold">
              ML-OS <span className="text-muted-foreground font-normal">© 2026</span>
            </span>
          </div>
          <p className="text-[10px] text-muted-foreground font-mono">
            Intelligent machine learning operating workspace environment.
          </p>
          <div className="flex items-center space-x-4">
            <a
              href="https://github.com/tvlswamy27/ml-os"
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground hover:text-foreground transition-colors"
              aria-label="GitHub Repository"
            >
              <svg className="h-4 w-4 fill-current hover:text-foreground" viewBox="0 0 24 24" aria-hidden="true">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.462-1.11-1.462-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.646.64.699 1.026 1.592 1.026 2.683 0 3.842-2.337 4.687-4.565 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.138 20.161 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
              </svg>
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};
export default MarketingShell;
