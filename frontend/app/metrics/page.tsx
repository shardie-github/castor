"use client";

import { useEffect, useState } from "react";
import { clsx } from "clsx";
import { Card } from "@/components/ui/card";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

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

interface DashboardMetrics {
  users: {
    dau: number;
    wau: number;
    mau: number;
    activation_rate: number;
    day_7_retention: number;
    day_30_retention: number;
  };
  revenue: {
    total_revenue: number;
    recurring_revenue: number;
    one_time_revenue: number;
    revenue_growth_rate: number;
    average_revenue_per_user: number;
    lifetime_value: number;
  };
  growth: {
    period: string;
    data: Array<{
      period: string;
      new_customers: number;
      revenue: number;
    }>;
  };
}

export default function MetricsDashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchMetrics() {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(`${apiUrl}/api/v1/metrics/dashboard`);
        
        if (!response.ok) {
          throw new Error("Failed to fetch metrics");
        }
        
        const data = await response.json();
        setMetrics(data);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
        setLoading(false);
      }
    }

    fetchMetrics();
  }, []);

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-2xl font-bold mb-6">Metrics Dashboard</h1>
        <div className="text-center">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-2xl font-bold mb-6">Metrics Dashboard</h1>
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-2xl font-bold mb-6">Metrics Dashboard</h1>
        <div>No metrics available</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Metrics Dashboard</h1>

      {/* Top-Level KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">MRR</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${metrics.revenue.recurring_revenue.toLocaleString()}
            </div>
            <div className="text-sm text-muted-foreground">
              {metrics.revenue.revenue_growth_rate > 0 ? "+" : ""}
              {metrics.revenue.revenue_growth_rate.toFixed(1)}% MoM
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">MAU</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics.users.mau.toLocaleString()}
            </div>
            <div className="text-sm text-muted-foreground">
              WAU: {metrics.users.wau.toLocaleString()} | DAU: {metrics.users.dau.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Activation Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics.users.activation_rate.toFixed(1)}%
            </div>
            <div className="text-sm text-muted-foreground">7-day activation</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Retention</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics.users.day_7_retention.toFixed(1)}%
            </div>
            <div className="text-sm text-muted-foreground">
              Day 7 | Day 30: {metrics.users.day_30_retention.toFixed(1)}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Revenue Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">ARPU</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${metrics.revenue.average_revenue_per_user.toFixed(2)}/mo
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">LTV</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${metrics.revenue.lifetime_value.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${metrics.revenue.total_revenue.toLocaleString()}
            </div>
            <div className="text-sm text-muted-foreground">
              Recurring: ${metrics.revenue.recurring_revenue.toLocaleString()}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Growth Chart */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Growth Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={metrics.growth.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="new_customers" stroke="#8884d8" name="New Customers" />
              <Line type="monotone" dataKey="revenue" stroke="#82ca9d" name="Revenue" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
