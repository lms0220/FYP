import { useState } from "react";
import {
  Shield,
  MessageSquare,
  Link as LinkIcon,
  Search,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { predictText } from "../api";

interface Example {
  id: number;
  label: string;
  description: string;
  content: string;
  type: "sms" | "url";
  expectedResult: "SAFE" | "MALICIOUS";
}

const safeExamples: Example[] = [
  {
    id: 1,
    label: "Legitimate Bank Website",
    description: "A real banking domain with secure HTTPS connection",
    content: "https://www.chase.com",
    type: "url",
    expectedResult: "SAFE",
  },
  {
    id: 3,
    label: "Bank OTP Code",
    description: "A legitimate SMS from your bank with a one-time password",
    content:
      "Your Chase verification code is: 847392. Never share this code. Chase will never ask for it.",
    type: "sms",
    expectedResult: "SAFE",
  },
  {
    id: 5,
    label: "Trusted Newsletter",
    description: "A legitimate subscription confirmation email link",
    content: "https://newsletter.techcrunch.com/verify?token=abc123xyz",
    type: "url",
    expectedResult: "SAFE",
  },
];

const maliciousExamples: Example[] = [
  {
    id: 2,
    label: "Fake Bank Login",
    description:
      "Phishing attempt impersonating a major bank with malicious domain",
    content: "http://suspicious-bank.xyz/verify?user=12345",
    type: "url",
    expectedResult: "MALICIOUS",
  },
  {
    id: 4,
    label: "Amazon Scam SMS",
    description: "SMS phishing asking to verify account with urgency tactics",
    content:
      "URGENT: Your Amazon account is suspended. Click here to verify: http://amaz0n-verify.ru/account",
    type: "sms",
    expectedResult: "MALICIOUS",
  },
  {
    id: 6,
    label: "Fake PayPal",
    description: "Credential harvesting site pretending to be PayPal login",
    content: "https://paypa1-security.com/login",
    type: "url",
    expectedResult: "MALICIOUS",
  },
];

export default function Submission() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<"sms" | "url">("sms");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadedExample, setLoadedExample] = useState<Example | null>(null);

  const instructions = {
    sms: "Paste a suspicious SMS message you received. Our AI will analyze it for phishing patterns, urgency tactics, and other threats.",
    url: "Paste a URL you want to verify. We'll check for malicious domains, suspicious patterns, and security threats.",
  };

  const handleExampleClick = (example: Example) => {
    setActiveTab(example.type);
    setInput(example.content);
    setLoadedExample(example);
  };

  const handleAnalyze = async () => {
    if (!input.trim()) {
      alert(`Please enter ${activeTab === "sms" ? "SMS message" : "URL"}`);
      return;
    }

    try {
      setLoading(true);
      const result = await predictText(input);
      const resultId = crypto.randomUUID?.() ?? String(Date.now());
      sessionStorage.setItem(
        `scamShieldResult-${resultId}`,
        JSON.stringify({ result, content: input }),
      );
      navigate(`/app/results/${resultId}`, {
        state: {
          result,
          content: input,
          expectedResult: loadedExample?.expectedResult,
        },
      });
    } catch (error) {
      console.log(error);
      alert(
        error instanceof Error ? error.message : "Cannot connect to backend",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* HEADER */}
      <div className="bg-gradient-to-r from-indigo-600 to-blue-600 rounded-2xl p-8 text-white shadow-lg">
        <h1 className="text-4xl font-bold">Scam & Phishing Detection</h1>
        <p className="mt-2 text-indigo-100">
          AI-powered analysis for suspicious SMS messages and URLs
        </p>
      </div>

      {/* TABBED INTERFACE */}
      <div className="bg-white rounded-xl shadow overflow-hidden">
        {/* Tabs */}
        <div className="flex border-b">
          <button
            onClick={() => {
              setActiveTab("sms");
              setInput("");
              setLoadedExample(null);
            }}
            className={`flex-1 py-4 px-6 font-semibold flex items-center justify-center gap-2 transition-colors ${
              activeTab === "sms"
                ? "bg-indigo-600 text-white"
                : "bg-gray-50 text-gray-700 hover:bg-gray-100"
            }`}
          >
            <MessageSquare size={20} />
            SMS Analysis
          </button>
          <button
            onClick={() => {
              setActiveTab("url");
              setInput("");
              setLoadedExample(null);
            }}
            className={`flex-1 py-4 px-6 font-semibold flex items-center justify-center gap-2 transition-colors ${
              activeTab === "url"
                ? "bg-indigo-600 text-white"
                : "bg-gray-50 text-gray-700 hover:bg-gray-100"
            }`}
          >
            <LinkIcon size={20} />
            URL Analysis
          </button>
        </div>

        {/* Content */}
        <div className="p-8 space-y-6">
          {/* Instructions */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-blue-900 text-sm">{instructions[activeTab]}</p>
          </div>

          {/* Input Area */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              {activeTab === "sms" ? "Paste SMS Message" : "Paste URL"}
            </label>
            <textarea
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                if (e.target.value !== loadedExample?.content) {
                  setLoadedExample(null);
                }
              }}
              placeholder={
                activeTab === "sms" ? "Enter SMS message..." : "Enter URL..."
              }
              className="w-full h-56 border-2 border-gray-300 rounded-lg p-4 font-mono text-sm focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 resize-none"
            />

            {/* Loaded Example Hint */}
            {loadedExample && (
              <div
                className={`mt-3 p-3 rounded-lg flex items-center gap-2 ${
                  loadedExample.expectedResult === "SAFE"
                    ? "bg-green-50 text-green-700 border border-green-200"
                    : "bg-red-50 text-red-700 border border-red-200"
                }`}
              >
                {loadedExample.expectedResult === "SAFE" ? (
                  <CheckCircle size={18} />
                ) : (
                  <AlertTriangle size={18} />
                )}
                <span className="text-sm font-semibold">
                  Example loaded — expected result:{" "}
                  <strong>{loadedExample.expectedResult}</strong>
                </span>
              </div>
            )}
          </div>

          {/* Buttons */}
          <div className="flex gap-4">
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Search size={20} />
              {loading ? "Analyzing..." : "Analyze with AI"}
            </button>
          </div>
        </div>
      </div>

      {/* TRY AN EXAMPLE SECTION */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-gray-900">Try an Example</h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* SAFE EXAMPLES */}
          <div className="bg-green-50 border-2 border-green-200 rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-3">
              <CheckCircle className="text-green-600" size={28} />
              <h3 className="text-xl font-bold text-green-900">
                Safe Examples
              </h3>
            </div>

            <div className="space-y-3">
              {safeExamples
                .filter((ex) => ex.type === activeTab)
                .map((example) => (
                  <button
                    key={example.id}
                    onClick={() => handleExampleClick(example)}
                    className="w-full text-left p-4 bg-white rounded-lg border border-green-200 hover:border-green-400 hover:shadow-md transition-all group"
                  >
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 group-hover:text-green-600">
                          {example.label}
                        </h4>
                        <p className="text-sm text-gray-600 mt-1">
                          {example.description}
                        </p>
                      </div>
                      <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded whitespace-nowrap">
                        Expected: Safe
                      </span>
                    </div>
                    <p className="text-xs bg-gray-50 p-2 rounded font-mono text-gray-700 break-all line-clamp-2">
                      {example.content}
                    </p>
                  </button>
                ))}
            </div>
          </div>

          {/* MALICIOUS EXAMPLES */}
          <div className="bg-red-50 border-2 border-red-200 rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="text-red-600" size={28} />
              <h3 className="text-xl font-bold text-red-900">
                Malicious Examples
              </h3>
            </div>

            <div className="space-y-3">
              {maliciousExamples
                .filter((ex) => ex.type === activeTab)
                .map((example) => (
                  <button
                    key={example.id}
                    onClick={() => handleExampleClick(example)}
                    className="w-full text-left p-4 bg-white rounded-lg border border-red-200 hover:border-red-400 hover:shadow-md transition-all group"
                  >
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 group-hover:text-red-600">
                          {example.label}
                        </h4>
                        <p className="text-sm text-gray-600 mt-1">
                          {example.description}
                        </p>
                      </div>
                      <span className="px-2 py-1 bg-red-100 text-red-700 text-xs font-semibold rounded whitespace-nowrap">
                        Expected: Threat
                      </span>
                    </div>
                    <p className="text-xs bg-gray-50 p-2 rounded font-mono text-gray-700 break-all line-clamp-2">
                      {example.content}
                    </p>
                  </button>
                ))}
            </div>
          </div>
        </div>
      </div>

      {/* INFO BOX */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-6">
        <div className="flex items-start gap-3">
          <Shield className="text-amber-600 flex-shrink-0 mt-1" size={24} />
          <div>
            <h3 className="font-bold text-amber-900">Keep yourself safe</h3>
            <ul className="text-amber-800 text-sm mt-2 space-y-1">
              <li>• Never click links from unknown sources</li>
              <li>
                • Be suspicious of urgent requests for personal information
              </li>
              <li>• Check domain spellings carefully</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
