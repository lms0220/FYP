import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { Shield, AlertTriangle, CheckCircle, ArrowLeft, Download, Share2, Search } from "lucide-react";
import { type PredictionResult } from "../api";

export default function Results() {
  const location = useLocation();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const initialResult = location.state?.result as PredictionResult | undefined;
  const initialContent = location.state?.content as string | undefined;
  const [savedResult, setSavedResult] = useState<PredictionResult | undefined>(initialResult);
  const [savedContent, setSavedContent] = useState<string | undefined>(initialContent);

  useEffect(() => {
    if (!initialResult && id) {
      const saved = sessionStorage.getItem(`scamShieldResult-${id}`);
      if (saved) {
        try {
          const parsed = JSON.parse(saved) as { result: PredictionResult; content: string };
          setSavedResult(parsed.result);
          setSavedContent(parsed.content);
        } catch {
          // ignore invalid saved state
        }
      }
    }
  }, [id, initialResult]);

  const result = savedResult;
  const submittedContent = savedContent;

  if (!result) {
    return (
      <div className="max-w-5xl mx-auto text-center py-12">
        <p className="text-gray-600 mb-4">No analysis result found for this report.</p>
        {id && <p className="text-sm text-gray-500 mb-4">Report ID: {id}</p>}
        <button
          onClick={() => navigate("/app/submit")}
          className="mt-4 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          Go Back
        </button>
      </div>
    );
  }

  const riskMessages: any = {
    no_https: "Website does not use a secure HTTPS connection",
    suspicious_tld: "Suspicious domain extension detected",
    url_shortener: "Shortened URL detected",
    suspicious_keywords: "Phishing-related keywords detected",
    ip_url: "URL uses an IP address instead of a trusted domain",
  };

  const handleDownloadReport = () => {
    const report = `
SCAM & PHISHING DETECTION REPORT
================================
Generated: ${new Date().toLocaleString()}

ANALYSIS RESULT: ${result.prediction}
Confidence Score: ${result.score}%
Input Type: ${result.type}

SUBMITTED CONTENT:
${submittedContent}

RISK FACTORS:
${result.flags?.map((flag) => `- ${riskMessages[flag] || flag}`).join("\n") || "None detected"}

RECOMMENDED ACTIONS:
${
  result.prediction === "SAFE"
    ? "- No significant threat detected. Continue normal usage."
    : "- Do not click suspicious links\n- Avoid sharing personal information\n- Verify information through official sources\n- Report suspicious messages"
}
    `;

    const blob = new Blob([report], { type: "text/plain" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `analysis-report-${Date.now()}.txt`;
    a.click();
  };

  const handleShareResults = () => {
    const shareText = `Scam & Phishing Detection Report\n${result.prediction}\nConfidence: ${result.score}%\nType: ${result.type}`;
    
    if (navigator.share) {
      navigator.share({
        title: "Scam & Phishing Detection Report",
        text: shareText,
      });
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(shareText);
      alert("Report copied to clipboard!");
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back Button */}
      <button
        onClick={() => navigate("/app/submit")}
        className="flex items-center gap-2 text-indigo-600 hover:text-indigo-800 font-semibold"
      >
        <ArrowLeft size={20} />
        Back
      </button>

      {/* Large Visual Result Header */}
      <div
        className={`
        rounded-2xl p-12 text-white shadow-xl
        ${result.prediction === "SAFE" ? "bg-gradient-to-r from-green-600 to-emerald-600" : "bg-gradient-to-r from-red-600 to-rose-600"}
      `}
      >
        <div className="flex items-center gap-6">
          {result.prediction === "SAFE" ? (
            <CheckCircle size={64} />
          ) : (
            <AlertTriangle size={64} />
          )}
          <div>
            <h1 className="text-5xl font-bold"># {result.prediction}</h1>
            <p className="mt-3 text-lg opacity-90">
              {result.prediction === "SAFE"
                ? "This content appears to be legitimate and safe"
                : "This content appears to be a scam or phishing attempt"}
            </p>
          </div>
        </div>
      </div>

      {/* Confidence Score with Animation */}
      <div className="bg-white rounded-xl shadow p-8">
        <h2 className="text-2xl font-bold mb-6">Confidence Score</h2>
        <div className="flex items-center gap-8">
          <div className="text-6xl font-bold text-indigo-600">{result.score}%</div>
          <div className="flex-1">
            <div className="bg-gray-200 rounded-full h-6 overflow-hidden">
              <div
                className={`h-full transition-all duration-1000 ease-out ${result.prediction === "SAFE" ? "bg-green-500" : "bg-red-500"}`}
                style={{ width: `${result.score}%` }}
              />
            </div>
            <p className="text-sm text-gray-600 mt-3">
              {result.prediction === "SAFE"
                ? "Content is verified as safe"
                : "Content flagged as malicious"}
            </p>
          </div>
        </div>
      </div>

      {/* Detailed Analysis */}
      <div className="bg-white rounded-xl shadow p-8">
        <h2 className="text-2xl font-bold mb-6">Analysis Details</h2>
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-gray-600 text-sm font-semibold">Content Type</p>
              <p className="text-2xl font-bold text-gray-900 mt-2">{result.type.toUpperCase()}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-gray-600 text-sm font-semibold">Risk Level</p>
              <p className={`text-2xl font-bold mt-2 ${result.prediction === "SAFE" ? "text-green-600" : "text-red-600"}`}>
                {result.prediction === "SAFE" ? "Low" : "High"}
              </p>
            </div>
          </div>
          
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-gray-600 text-sm font-semibold mb-2">Full Submitted Content</p>
            <p className="text-sm bg-white p-4 rounded border border-gray-200 font-mono break-all">{submittedContent}</p>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <p className="text-gray-600 text-sm font-semibold">Analysis Time</p>
              <p className="text-sm text-gray-900 mt-2">{new Date().toLocaleString()}</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm font-semibold">Category</p>
              <p className="text-sm text-gray-900 mt-2">
                {result.prediction === "SAFE" ? "Legitimate Content" : "Phishing/Malicious"}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Threat Indicators or Safety Indicators */}
      {result.flags && result.flags.length > 0 && result.prediction !== "SAFE" ? (
        <div className="bg-white rounded-xl shadow p-8">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <AlertTriangle className="text-red-600" size={28} />
            Detected Threats
          </h2>
          <div className="space-y-3">
            {result.flags.map((flag: string) => (
              <div key={flag} className="flex items-start gap-4 p-4 bg-red-50 rounded-lg border border-red-200">
                <AlertTriangle className="text-red-600 flex-shrink-0 mt-0.5" size={24} />
                <span className="text-red-700 font-semibold">{riskMessages[flag] || flag}</span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow p-8">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <CheckCircle className="text-green-600" size={28} />
            Safety Indicators
          </h2>
          <div className="p-4 bg-green-50 rounded-lg border border-green-200">
            <p className="text-green-700 font-semibold">✓ No threats detected</p>
            <p className="text-green-600 text-sm mt-2">This content passed all security checks</p>
          </div>
        </div>
      )}

      {/* Recommended Actions */}
      <div className="bg-amber-50 border-2 border-amber-200 rounded-xl p-8">
        <div className="flex items-center gap-3 mb-6">
          <Shield className="text-amber-600" size={32} />
          <h2 className="text-2xl font-bold text-amber-900">Recommended Actions</h2>
        </div>

        {result.prediction === "SAFE" ? (
          <p className="text-amber-900 text-lg">No significant threat detected. Continue normal usage.</p>
        ) : (
          <ul className="space-y-3 text-amber-900">
            <li className="flex items-start gap-3">
              <span className="font-bold text-xl">•</span>
              <span className="text-base">Do not click any links or provide personal information</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="font-bold text-xl">•</span>
              <span className="text-base">Delete the message immediately</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="font-bold text-xl">•</span>
              <span className="text-base">Report to your email provider or mobile carrier</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="font-bold text-xl">•</span>
              <span className="text-base">Block the sender if possible</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="font-bold text-xl">•</span>
              <span className="text-base">Monitor your accounts for suspicious activity</span>
            </li>
          </ul>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 pb-8">
        <button
          onClick={() => navigate("/app/submit")}
          className="flex items-center justify-center gap-2 flex-1 px-6 py-4 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Search size={20} />
          Analyze Another
        </button>
        <button
          onClick={handleDownloadReport}
          className="flex items-center justify-center gap-2 px-6 py-4 bg-gray-600 text-white font-semibold rounded-lg hover:bg-gray-700 transition-colors"
        >
          <Download size={20} />
          Download Report
        </button>
        <button
          onClick={handleShareResults}
          className="flex items-center justify-center gap-2 px-6 py-4 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Share2 size={20} />
          Share Results
        </button>
      </div>
    </div>
  );
}
