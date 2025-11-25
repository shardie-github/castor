"use client";

import { useState } from "react";
import { clsx } from "clsx";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Copy, Share2, Lock, Globe } from "lucide-react";

// Card sub-components
const CardHeader = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={clsx("px-6 py-4 border-b border-gray-200", className)}>{children}</div>
);
const CardContent = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={clsx("px-6 py-4", className)}>{children}</div>
);
const CardTitle = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <h3 className={clsx("text-lg font-semibold", className)}>{children}</h3>
);

interface ShareReportProps {
  reportId: string;
}

export default function ReportShare({ reportId }: ShareReportProps) {
  const [shareToken, setShareToken] = useState<string | null>(null);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [accessLevel, setAccessLevel] = useState<"public" | "password_protected">("public");
  const [password, setPassword] = useState("");
  const [expiresDays, setExpiresDays] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleShare = async () => {
    setLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/v1/reports/${reportId}/share`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          access_level: accessLevel,
          password: accessLevel === "password_protected" ? password : undefined,
          expires_days: expiresDays || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to create share link");
      }

      const data = await response.json();
      setShareToken(data.share_token);
      setShareUrl(data.share_url);
    } catch (error) {
      console.error("Error sharing report:", error);
      alert("Failed to create share link");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (shareUrl) {
      navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Share2 className="h-5 w-5" />
          Share Report
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {!shareUrl ? (
          <>
            <div className="space-y-2">
              <Label>Access Level</Label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    value="public"
                    checked={accessLevel === "public"}
                    onChange={(e) => setAccessLevel(e.target.value as "public")}
                  />
                  <Globe className="h-4 w-4" />
                  Public
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    value="password_protected"
                    checked={accessLevel === "password_protected"}
                    onChange={(e) => setAccessLevel(e.target.value as "password_protected")}
                  />
                  <Lock className="h-4 w-4" />
                  Password Protected
                </label>
              </div>
            </div>

            {accessLevel === "password_protected" && (
              <div className="space-y-2">
                <Label>Password</Label>
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                />
              </div>
            )}

            <div className="space-y-2">
              <Label>Expires In (Days) - Optional</Label>
              <Input
                type="number"
                value={expiresDays || ""}
                onChange={(e) => setExpiresDays(e.target.value ? parseInt(e.target.value) : null)}
                placeholder="Leave empty for no expiration"
              />
            </div>

            <Button onClick={handleShare} disabled={loading}>
              {loading ? "Creating..." : "Create Share Link"}
            </Button>
          </>
        ) : (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Share Link</Label>
              <div className="flex gap-2">
                <Input value={shareUrl} readOnly className="flex-1" />
                <Button onClick={handleCopy} variant="outline">
                  {copied ? "Copied!" : <Copy className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            <div className="text-sm text-muted-foreground">
              Anyone with this link can view the report
              {accessLevel === "password_protected" && " (password required)"}
            </div>

            <Button
              variant="outline"
              onClick={() => {
                setShareUrl(null);
                setShareToken(null);
              }}
            >
              Create New Link
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
