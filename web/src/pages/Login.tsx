import * as React from "react";
import { useNavigate, Link } from "react-router-dom";
import { FolderDot, Lock, Mail } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter, CardDescription } from "../components/Card";
import { Button } from "../components/Button";
import { Input } from "../components/Input";
import { useAuth, useToast } from "../hooks";
import { ApiRequestError } from "../services/apiClient";

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [email, setEmail] = React.useState("engineer@mlos.org");
  const [password, setPassword] = React.useState("password");
  const { loginMutation } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast("Please enter your email and password", "error");
      return;
    }

    try {
      await loginMutation.mutateAsync({ email, password });
      toast("Successfully authenticated in session", "success");
      navigate("/workspace");
    } catch (err: any) {
      if (err instanceof ApiRequestError) {
        toast(err.message, "error");
      } else {
        toast(err.message || "Failed to authenticate", "error");
      }
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 select-none">
      <Card className="w-full max-w-sm bg-card/45 border-border shadow-lg">
        <CardHeader className="text-center space-y-2 pb-6 border-b border-border/10">
          <div className="flex justify-center mb-1">
            <div className="p-1.5 rounded bg-primary/10 border border-primary/20">
              <FolderDot className="h-5 w-5 text-primary" />
            </div>
          </div>
          <CardTitle className="text-md font-bold tracking-tight text-foreground">Welcome Back</CardTitle>
          <CardDescription>Enter details to open your ML-OS studio workspace.</CardDescription>
        </CardHeader>
        
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4 pt-6 text-left">
            {/* Email */}
            <div className="space-y-1.5">
              <label htmlFor="email" className="text-xs font-mono font-medium text-muted-foreground">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  className="pl-10 text-xs h-9"
                  placeholder="engineer@mlos.org"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <label htmlFor="password" className="text-xs font-mono font-medium text-muted-foreground">
                  Password
                </label>
                <Link to="/forgot-password" className="text-[10px] text-primary hover:underline">
                  Forgot?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  className="pl-10 text-xs h-9"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>
          </CardContent>

          <CardFooter className="flex flex-col space-y-3 pt-2">
            <Button type="submit" disabled={loginMutation.isPending} className="w-full text-xs h-9">
              {loginMutation.isPending ? "Authenticating..." : "Sign In"}
            </Button>
            <div className="text-[11px] text-muted-foreground text-center">
              Don't have a workspace?{" "}
              <Link to="/signup" className="text-primary hover:underline">
                Create account
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};
export default Login;
