import * as React from "react";
import { useNavigate, Link } from "react-router-dom";
import { FolderDot, Lock, Mail, User } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter, CardDescription } from "../components/Card";
import { Button } from "../components/Button";
import { Input } from "../components/Input";
import { useAuth, useToast } from "../hooks";
import { ApiRequestError } from "../services/apiClient";

export const Signup: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [name, setName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const { signupMutation, loginMutation } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || !confirmPassword) {
      toast("Please populate all registration fields", "error");
      return;
    }

    if (password !== confirmPassword) {
      toast("Passwords do not match", "error");
      return;
    }

    try {
      // 1. Create account
      await signupMutation.mutateAsync({ email, password });
      // 2. Perform auto-login
      await loginMutation.mutateAsync({ email, password });
      
      toast("Workspace account created successfully", "success");
      navigate("/workspace");
    } catch (err: any) {
      if (err instanceof ApiRequestError) {
        toast(err.message, "error");
      } else {
        toast(err.message || "Failed to create account", "error");
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
          <CardTitle className="text-md font-bold tracking-tight text-foreground">Create Workspace</CardTitle>
          <CardDescription>Configure your ML-OS development account.</CardDescription>
        </CardHeader>
        
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4 pt-6 text-left">
            {/* Name */}
            <div className="space-y-1.5">
              <label htmlFor="name" className="text-xs font-mono font-medium text-muted-foreground">
                Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="name"
                  type="text"
                  className="pl-10 text-xs h-9"
                  placeholder="Vikram Tanakala"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
            </div>

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
              <label htmlFor="password" className="text-xs font-mono font-medium text-muted-foreground">
                Password
              </label>
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

            {/* Confirm Password */}
            <div className="space-y-1.5">
              <label htmlFor="confirmPassword" className="text-xs font-mono font-medium text-muted-foreground">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="confirmPassword"
                  type="password"
                  className="pl-10 text-xs h-9"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>
            </div>
          </CardContent>

          <CardFooter className="flex flex-col space-y-3 pt-2">
            <Button type="submit" disabled={signupMutation.isPending || loginMutation.isPending} className="w-full text-xs h-9">
              {signupMutation.isPending || loginMutation.isPending ? "Creating..." : "Create Account"}
            </Button>
            <div className="text-[11px] text-muted-foreground text-center">
              Already have an account?{" "}
              <Link to="/login" className="text-primary hover:underline">
                Sign In
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};
export default Signup;
