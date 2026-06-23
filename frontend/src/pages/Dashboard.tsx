import { type ReactNode, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle,
  ArrowRight,
  CalendarDays,
  FolderOpen,
} from "lucide-react";
import { getHistory, type HistoryItem } from "../api";

type DashboardStat = {
  label: string;
  value: number;
  color: string;
  icon: ReactNode;
};

type ActivityItem = {
  id: string;
  type: "sms" | "url";
  classification: "SAFE" | "MALICIOUS";
  content: string;
  confidence: number;
  createdAt: string;
};

const initialStats = {
  total: 0,
  malicious: 0,
  safe: 0,
  thisWeek: 0,
};


function formatRelativeTime(dateString: string) {
  const date = new Date(dateString);
  const diffMs = Date.now() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMinutes < 60) {
    return `${diffMinutes} minutes ago`;
  }

  if (diffHours < 24) {
    return `${diffHours} hours ago`;
  }

  return `${diffDays} days ago`;
}

export default function Dashboard() {
  const navigate = useNavigate();

  const [dashboardStats, setDashboardStats] = useState(initialStats);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [username, setUsername] = useState("John");

  useEffect(() => {
    const storedName = sessionStorage.getItem("scamShieldUsername");
    if (storedName) {
      setUsername(storedName);
    }
    getHistory()
      .then((results: HistoryItem[]) => {
        const total = results.length;
        const malicious = results.filter((item) => item.classification !== "SAFE").length;
        const safe = results.filter((item) => item.classification === "SAFE").length;
        const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
        const thisWeek = results.filter((item) => new Date(item.created_at) >= oneWeekAgo).length;

        const recent = results.slice(0, 4).map((item) => ({
          id: item.result_id,
          type: item.type,
          classification: (item.classification === "SAFE" ? "SAFE" : "MALICIOUS") as "SAFE" | "MALICIOUS",
          content: item.content,
          confidence: Number(item.confidence_score),
          createdAt: item.created_at,
        }));

        setDashboardStats({
          total,
          malicious,
          safe,
          thisWeek,
        });
        setActivity(recent);
      })
      .catch((err) => {
        console.error(err);
      });
  }, []);

  const stats: DashboardStat[] = [
    {
      label: "Total Scans",
      value: dashboardStats.total,
      color: "bg-blue-100 text-blue-700",
      icon: <FolderOpen className="w-6 h-6 text-blue-600" />,
    },
    {
      label: "Threats Detected",
      value: dashboardStats.malicious,
      color: "bg-red-100 text-red-700",
      icon: <AlertTriangle className="w-6 h-6 text-red-600" />,
    },
    {
      label: "Safe Items",
      value: dashboardStats.safe,
      color: "bg-green-100 text-green-700",
      icon: <CheckCircle className="w-6 h-6 text-green-600" />,
    },
    {
      label: "This Week",
      value: dashboardStats.thisWeek,
      color: "bg-indigo-100 text-indigo-700",
      icon: <CalendarDays className="w-6 h-6 text-indigo-600" />,
    },
  ];

  return (
    <div className="space-y-8 p-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-indigo-600 to-blue-600 rounded-2xl shadow-lg p-8 text-white">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-indigo-100/80">
              Welcome back, {username}!
            </p>
            <h1 className="text-4xl font-bold mt-3">AI-powered phishing protection</h1>
            <p className="mt-3 max-w-2xl text-indigo-100/90">
              Stay ahead of scams with fast URL and SMS analysis, history tracking, and intelligent threat detection.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => navigate("/app/submit")}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-indigo-700 rounded-xl font-semibold shadow-sm hover:bg-gray-100 transition"
            >
              Submit for Analysis
            </button>
            <button
              onClick={() => navigate("/app/history")}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-white/20 text-white rounded-xl font-semibold hover:bg-white/10 transition"
            >
              View History
            </button>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white rounded-3xl shadow-sm p-6 flex items-center justify-between gap-4">
            <div>
              <p className="text-sm text-gray-500">{stat.label}</p>
              <p className="mt-3 text-4xl font-bold text-gray-900">{stat.value.toLocaleString()}</p>
            </div>
            <div className={`inline-flex items-center justify-center w-14 h-14 rounded-2xl ${stat.color}`}>
              {stat.icon}
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-3xl shadow-sm p-6">
        <div className="flex items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Recent Activity</h2>
            <p className="text-sm text-gray-500 mt-1">
              Latest scans from your account.
            </p>
          </div>
          <button
            onClick={() => navigate("/app/history")}
            className="inline-flex items-center gap-2 text-sm font-semibold text-indigo-600 hover:text-indigo-800"
          >
            View All
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        <div className="grid gap-4">
          {activity.map((item) => (
            <button
              key={item.id}
              onClick={() => navigate(`/app/results/${item.id}`, { state: { result: {
                type: item.type,
                prediction: item.classification,
                score: item.confidence,
                flags: item.classification === "SAFE" ? [] : ["suspicious_keywords"],
                message: item.content,
              }, content: item.content } })}
              className="w-full bg-gray-50 border border-gray-200 rounded-3xl p-5 text-left hover:border-indigo-300 hover:shadow-md transition"
            >
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                <div className="flex-1">
                  <div className="flex flex-wrap gap-2 items-center mb-3">
                    <span className="inline-flex items-center px-3 py-1 rounded-full bg-gray-100 text-gray-700 text-xs font-semibold uppercase tracking-[0.16em]">
                      {item.type.toUpperCase()}
                    </span>
                    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold ${
                      item.classification === "SAFE"
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}>
                      {item.classification === "SAFE" ? (
                        <CheckCircle className="w-3.5 h-3.5" />
                      ) : (
                        <AlertTriangle className="w-3.5 h-3.5" />
                      )}
                      {item.classification === "SAFE" ? "Safe" : "Malicious"}
                    </span>
                  </div>
                  <p className="text-gray-900 font-semibold truncate max-w-3xl">
                    {item.content}
                  </p>
                </div>

                <div className="flex items-center gap-4">
                  <div className="hidden sm:flex flex-col text-right">
                    <span className="text-sm text-gray-500">{formatRelativeTime(item.createdAt)}</span>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-gray-900">{item.confidence}%</p>
                    <span className="text-sm text-gray-500">Confidence</span>
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Stay Safe Online Tips */}
      <div className="bg-amber-50 border border-amber-200 rounded-3xl p-6">
        <h3 className="text-xl font-bold text-amber-900 mb-4">Stay Safe Online</h3>
        <ul className="space-y-3 text-amber-950 text-sm">
          <li>• Don't share personal info via SMS or suspicious links.</li>
          <li>• Verify the sender before clicking anything.</li>
          <li>• Use the AI scanner for suspicious content.</li>
          <li>• Enable two-factor authentication.</li>
        </ul>
      </div>
    </div>
  );
}
