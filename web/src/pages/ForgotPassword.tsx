import * as React from "react";
import { useNavigate, Link } from "react-router-dom";
import { FolderDot, Mail } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter, CardDescription } from "../components/Card";
import { Button } from "../components/Button";
import { Input } from "../components/Input";
import { useToast } from "../hooks";

export const ForgotPassword: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [email, setEmail] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      toast("Please enter your email address", "error");
      return;
    }

    setIsLoading(true);
    // Simulate reset email
    setTimeout(() => {
      setIsLoading(false);
      toast("Password reset instructions dispatched", "success");
      navigate("/login");
    }, 800);
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
          <CardTitle className="text-md font-bold tracking-tight text-foreground">Recover Password</CardTitle>
          <CardDescription>Enter email to receive reset credentials.</CardDescription>
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
          </CardContent>

          <CardFooter className="flex flex-col space-y-3 pt-2">
            <Button type="submit" disabled={isLoading} className="w-full text-xs h-9">
              {isLoading ? "Sending instructions..." : "Send Reset Code"}
            </Button>
            <div className="text-[11px] text-muted-foreground text-center">
              Remember credentials?{" "}
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
export default ForgotPassword;
