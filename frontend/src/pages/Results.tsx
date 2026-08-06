import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  ArrowLeft,
  Download,
  Share2,
  Search,
} from "lucide-react";
import { type PredictionResult } from "../api";
import jsPDF from "jspdf";

export default function Results() {
  const location = useLocation();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const initialResult = location.state?.result as PredictionResult | undefined;
  const initialContent = location.state?.content as string | undefined;

  const [savedResult, setSavedResult] = useState<
    PredictionResult | undefined
  >(initialResult);

  const [savedContent, setSavedContent] = useState<string | undefined>(
    initialContent,
  );

  useEffect(() => {
    if (!initialResult && id) {
      const saved = sessionStorage.getItem(
        `scamShieldResult-${id}`,
      );

      if (saved) {
        try {
          const parsed = JSON.parse(saved) as {
            result: PredictionResult;
            content: string;
          };

          setSavedResult(parsed.result);
          setSavedContent(parsed.content);

        } catch {
          console.log("Invalid saved result");
        }
      }
    }
  }, [id, initialResult]);


  const result = savedResult;
  const submittedContent = savedContent;


  if (!result) {
    return (
      <div className="max-w-5xl mx-auto text-center py-12">

        <p className="text-black mb-4">
          No analysis result found for this report.
        </p>


        {id && (
          <p className="text-sm text-gray-500 mb-4">
            Report ID: {id}
          </p>
        )}


        <button
          onClick={() => navigate("/app/submit")}
          className="mt-4 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          Go Back
        </button>

      </div>
    );
  }



  const riskMessages: Record<string, string> = {

    no_https:
      "Website does not use a secure HTTPS connection",

    suspicious_tld:
      "Suspicious domain extension detected",

    url_shortener:
      "Shortened URL detected",

    suspicious_keywords:
      "Phishing-related keywords detected",

    ip_url:
      "URL uses an IP address instead of a trusted domain",

  };



  const handleDownloadReport = () => {

    const doc = new jsPDF();


    doc.setFontSize(18);

    doc.text(
      "Scam Shield AI Analysis Report",
      20,
      20
    );


    doc.setFontSize(12);


    doc.text(
      `Generated: ${new Date().toLocaleString()}`,
      20,
      35
    );


    doc.text(
      `Prediction: ${result.prediction}`,
      20,
      50
    );


    doc.text(
      `Confidence: ${result.score ?? 0}%`,
      20,
      60
    );


    doc.text(
      `Type: ${result.type}`,
      20,
      70
    );


    doc.text(
      "Submitted Content:",
      20,
      90
    );


    doc.text(
      doc.splitTextToSize(
        submittedContent || "",
        170
      ),
      20,
      100
    );


    let y = 140;


    doc.text(
      "Threat Indicators:",
      20,
      y
    );


    y += 10;


    if (result.flags && result.flags.length > 0) {

      result.flags.forEach((flag) => {

        doc.text(
          "- " + (riskMessages[flag] || flag),
          25,
          y
        );

        y += 10;

      });


    } else {

      doc.text(
        "No threats detected.",
        25,
        y
      );

      y += 10;

    }



    y += 10;


    doc.text(
      "Recommended Actions:",
      20,
      y
    );


    y += 10;



    if (result.prediction === "SAFE") {

      doc.text(
        "Continue normal usage.",
        25,
        y
      );


    } else {

      doc.text(
        "Do not click suspicious links.",
        25,
        y
      );

      y += 10;


      doc.text(
        "Avoid sharing personal information.",
        25,
        y
      );

      y += 10;


      doc.text(
        "Delete the message immediately.",
        25,
        y
      );

    }


    doc.save(
      `Analysis_Report_${Date.now()}.pdf`
    );

  };



  const handleShareResults = () => {

    const shareText =
      `Scam & Phishing Detection Report\n\n` +
      `Prediction: ${result.prediction}\n` +
      `Confidence: ${result.score}%\n` +
      `Type: ${result.type}`;


    if (navigator.share) {

      navigator.share({

        title:
          "Scam & Phishing Detection Report",

        text:
          shareText,

      });


    } else {

      navigator.clipboard.writeText(
        shareText
      );

      alert(
        "Report copied to clipboard!"
      );

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



      {/* Result Header */}
      <div
        className={`
          rounded-2xl p-12 text-white shadow-xl
          ${
            result.prediction === "SAFE"
              ? "bg-gradient-to-r from-green-600 to-emerald-600"
              : "bg-gradient-to-r from-red-600 to-rose-600"
          }
        `}
      >

        <div className="flex items-center gap-6">

          {
            result.prediction === "SAFE"
              ? <CheckCircle size={64} />
              : <AlertTriangle size={64} />
          }


          <div>

            <h1 className="text-5xl font-bold">
              # {result.prediction}
            </h1>


            <p className="mt-3 text-lg opacity-90">

              {
                result.prediction === "SAFE"
                  ? "This content appears to be legitimate and safe"
                  : "This content appears to be a scam or phishing attempt"
              }

            </p>

          </div>

        </div>

      </div>





      {/* Confidence Score */}
      <div className="bg-white rounded-xl shadow p-8">

        <h2 className="text-2xl font-bold mb-6">
          Detection Confidence
        </h2>


        <div className="flex items-center gap-8">


          <div className="text-6xl font-bold text-indigo-600">

            {result.score}%

          </div>



          <div className="flex-1">


            <div className="bg-gray-200 rounded-full h-6 overflow-hidden">

              <div

                className={`
                  h-full transition-all duration-1000 ease-out
                  ${
                    result.prediction === "SAFE"
                      ? "bg-green-500"
                      : "bg-red-500"
                  }
                `}

                style={{
                  width: `${result.score}%`,
                }}

              />

            </div>



            <p className="text-sm text-black mt-3">

              {
                result.prediction === "SAFE"
                  ? "Content is verified as safe"
                  : "Content flagged as malicious"
              }

            </p>


          </div>


        </div>

      </div>





      {/* AI Security Analysis */}

      {
        result.llm_analysis && (

          <div className="bg-white rounded-xl shadow p-8">


            <h2 className="text-2xl font-bold mb-6">

              AI Security Analysis

            </h2>



            <div className="space-y-5">

              {result.llm_analysis.explanation && (
                <div className="rounded-lg border border-indigo-100 bg-indigo-50 p-4 text-indigo-950">
                  <p className="font-semibold mb-1">AI Security Explanation</p>
                  <p>{result.llm_analysis.explanation}</p>
                </div>
              )}



              <div>

                <p className="font-semibold">
                  Threat Type
                </p>


                <p>
                  {
                    result.llm_analysis.threat_type ||
                    "Not available"
                  }
                </p>

              </div>





              {result.llm_analysis.target_organization && (
              <div>

                <p className="font-semibold">
                  Impersonated Organization
                </p>

                <p>{result.llm_analysis.target_organization}</p>

              </div>
              )}

              <div>

                <p className="font-semibold">
                  Risk Level
                </p>


                <p>
                  {
                    result.risk_level ||
                    result.llm_analysis.risk_level ||
                    "Not available"
                  }
                </p>

              </div>


              <div>

                <p className="font-semibold">
                  Recommendation
                </p>


                <p>

                  {
                    result.llm_analysis.recommendation ||
                    "No recommendation available."
                  }

                </p>


              </div>



            </div>


          </div>

        )
      }





      {/* Analysis Details */}

      <div className="bg-white rounded-xl shadow p-8">


        <h2 className="text-2xl font-bold mb-6">

          Analysis Details

        </h2>



        <div className="space-y-6">



          <div className="grid grid-cols-2 gap-6">


            <div className="bg-gray-50 p-4 rounded-lg">

              <p className="text-black text-sm font-semibold">

                Content Type

              </p>


              <p className="text-2xl font-bold text-gray-900 mt-2">

                {
                  result.type?.toUpperCase() ||
                  "UNKNOWN"
                }

              </p>


            </div>





            <div className="bg-gray-50 p-4 rounded-lg">


              <p className="text-black text-sm font-semibold">

                Risk Level

              </p>



              <p
                className={`
                  text-2xl font-bold mt-2
                  ${
                    result.prediction === "SAFE"
                      ? "text-green-600"
                      : "text-red-600"
                  }
                `}
              >

                {
                  result.prediction === "SAFE"
                    ? "Low"
                    : "High"
                }


              </p>


            </div>


          </div>





          <div className="bg-gray-50 p-4 rounded-lg">


            <p className="text-black text-sm font-semibold mb-2">

              Full Submitted Content

            </p>



            <p className="text-sm bg-white p-4 rounded border border-gray-200 font-mono break-all">

              {
                submittedContent
              }

            </p>


          </div>





          <div className="grid grid-cols-2 gap-6">


            <div>

              <p className="text-black text-sm font-semibold">

                Analysis Time

              </p>


              <p className="text-sm text-gray-900 mt-2">

                {
                  new Date().toLocaleString()
                }

              </p>


            </div>





            <div>

              <p className="text-black text-sm font-semibold">

                Category

              </p>


              <p className="text-sm text-gray-900 mt-2">

                {
                  result.prediction === "SAFE"
                    ? "Legitimate Content"
                    : "Phishing/Malicious"
                }

              </p>


            </div>


          </div>


        </div>


      </div>

            {/* Threat Indicators / Safety Indicators */}

      {
        result.flags &&
        result.flags.length > 0 &&
        result.prediction !== "SAFE"

        ? (

          <div className="bg-white rounded-xl shadow p-8">


            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">

              <AlertTriangle
                className="text-red-600"
                size={28}
              />

              Detected Threats

            </h2>



            <div className="space-y-3">


              {
                result.risk_factors && result.risk_factors.length > 0

                ? result.risk_factors.map((factor) => (

                  <div
                    key={factor.code}
                    className="flex items-start gap-4 p-4 bg-red-50 rounded-lg border border-red-200"
                  >

                    <AlertTriangle
                      className="text-red-600 flex-shrink-0 mt-0.5"
                      size={24}
                    />

                    <span className="text-red-800">
                      <strong>{factor.title} (+{factor.points})</strong>
                      <br />
                      <span className="text-sm">{factor.detail}</span>
                    </span>

                  </div>

                ))

                : result.flags.map((flag: string) => (

                  <div
                    key={flag}
                    className="
                      flex items-start gap-4
                      p-4
                      bg-red-50
                      rounded-lg
                      border border-red-200
                    "
                  >


                    <AlertTriangle
                      className="text-red-600 flex-shrink-0 mt-0.5"
                      size={24}
                    />



                    <span className="text-red-700 font-semibold">

                      {
                        riskMessages[flag] || flag
                      }

                    </span>


                  </div>

                ))
              }


            </div>


          </div>

        )

        : (

          <div className="bg-white rounded-xl shadow p-8">


            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">


              <CheckCircle
                className="text-green-600"
                size={28}
              />


              Safety Indicators


            </h2>



            <div
              className="
                p-4
                bg-green-50
                rounded-lg
                border border-green-200
              "
            >


              <p className="text-green-700 font-semibold">

                ✓ No threats detected

              </p>



              <p className="text-green-600 text-sm mt-2">

                This content passed all security checks

              </p>


            </div>


          </div>

        )

      }






      {/* Recommended Actions */}

      <div
        className="
          bg-amber-50
          border-2
          border-amber-200
          rounded-xl
          p-8
        "
      >


        <div className="flex items-center gap-3 mb-6">


          <Shield
            className="text-amber-600"
            size={32}
          />


          <h2 className="text-2xl font-bold text-amber-900">

            Recommended Actions

          </h2>


        </div>





        {
          result.prediction === "SAFE"

          ? (

            <p className="text-amber-900 text-lg">

              No significant threat detected. Continue normal usage.

            </p>

          )

          : (

            <ul className="space-y-3 text-amber-900">


              <li className="flex items-start gap-3">

                <span className="font-bold text-xl">
                  •
                </span>


                <span className="text-base">

                  {result.type === "url" ? "Do not open the URL or enter credentials" : "Do not click links or provide personal information"}

                </span>


              </li>





              <li className="flex items-start gap-3">

                <span className="font-bold text-xl">
                  •
                </span>


                <span className="text-base">

                  {result.type === "url" ? "Access the claimed organization through its official website" : "Delete the message immediately"}

                </span>


              </li>





              <li className="flex items-start gap-3">

                <span className="font-bold text-xl">
                  •
                </span>


                <span className="text-base">

                  {result.type === "url" ? "Remove the suspicious message containing the link" : "Report to your email provider or mobile carrier"}

                </span>


              </li>





              <li className="flex items-start gap-3">

                <span className="font-bold text-xl">
                  •
                </span>


                <span className="text-base">

                  {result.type === "url" ? "Report the phishing website to your browser or a security service" : "Block the sender if possible"}

                </span>


              </li>





              <li className="flex items-start gap-3">

                <span className="font-bold text-xl">
                  •
                </span>


                <span className="text-base">

                  Monitor your accounts for suspicious activity

                </span>


              </li>


            </ul>

          )

        }


      </div>






      {/* Action Buttons */}

      <div className="flex gap-3 pb-8">


        <button
          onClick={() => navigate("/app/submit")}
          className="
            flex items-center justify-center gap-2
            flex-1
            px-6
            py-4
            bg-indigo-600
            text-white
            font-semibold
            rounded-lg
            hover:bg-indigo-700
            transition-colors
          "
        >

          <Search size={20} />

          Analyze Another

        </button>





        <button
          onClick={handleDownloadReport}
          className="
            flex items-center justify-center gap-2
            px-6
            py-4
            bg-gray-600
            text-white
            font-semibold
            rounded-lg
            hover:bg-gray-700
            transition-colors
          "
        >

          <Download size={20} />

          Download Report

        </button>





        <button
          onClick={handleShareResults}
          className="
            flex items-center justify-center gap-2
            px-6
            py-4
            bg-blue-600
            text-white
            font-semibold
            rounded-lg
            hover:bg-blue-700
            transition-colors
          "
        >

          <Share2 size={20} />

          Share Results

        </button>


      </div>


    </div>
  );
}
