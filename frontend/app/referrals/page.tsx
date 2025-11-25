"use client";

import { useEffect, useState } from "react";
import { clsx } from "clsx";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Copy, Share2, Users } from "lucide-react";

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

interface ReferralData {
  code: string;
  referral_url: string;
  total_referrals: number;
  completed_referrals: number;
}

export default function ReferralsPage() {
  const [referralData, setReferralData] = useState<ReferralData | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchReferralCode() {
      try {
        // Get current user ID (would come from auth context in production)
        const userId = "current-user-id"; // TODO: Get from auth context

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(`${apiUrl}/api/v1/referrals/${userId}`);

        if (!response.ok) {
          throw new Error("Failed to fetch referral code");
        }

        const data = await response.json();
        setReferralData(data);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
        setLoading(false);
      }
    }

    fetchReferralCode();
  }, []);

  const handleCopy = () => {
    if (referralData?.referral_url) {
      navigator.clipboard.writeText(referralData.referral_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-2xl font-bold mb-6">Referral Program</h1>
        <div>Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-2xl font-bold mb-6">Referral Program</h1>
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  if (!referralData) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-2xl font-bold mb-6">Referral Program</h1>
        <div>No referral data available</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Referral Program</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Share2 className="h-5 w-5" />
              Your Referral Code
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Referral Code</Label>
              <div className="flex gap-2">
                <Input value={referralData.code} readOnly className="font-mono text-lg" />
                <Button onClick={handleCopy} variant="outline">
                  {copied ? "Copied!" : <Copy className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Referral Link</Label>
              <div className="flex gap-2">
                <Input value={referralData.referral_url} readOnly className="flex-1" />
                <Button onClick={handleCopy} variant="outline">
                  {copied ? "Copied!" : <Copy className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            <div className="text-sm text-muted-foreground">
              Share this link with other podcasters. When they sign up, you both get rewards!
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Referral Stats
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="text-2xl font-bold">{referralData.completed_referrals}</div>
                <div className="text-sm text-muted-foreground">Completed Referrals</div>
              </div>
              <div>
                <div className="text-2xl font-bold">{referralData.total_referrals}</div>
                <div className="text-sm text-muted-foreground">Total Referrals</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>How It Works</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="list-decimal list-inside space-y-2">
            <li>Share your referral link with other podcasters</li>
            <li>When they sign up using your link, they get [reward]</li>
            <li>You get [reward] for each successful referral</li>
            <li>Track your referrals and rewards here</li>
          </ol>
        </CardContent>
      </Card>
    </div>
  );
}
