import { useEffect, useState } from "react";
import {
  History as HistoryIcon,
  AlertTriangle,
  CheckCircle,
  Search,
  Download,
  Trash2,
} from "lucide-react";
import { getHistory, type HistoryItem } from "../api";

type FilterType = "all" | "malicious" | "safe";

export default function History() {
  const [searchTerm, setSearchTerm] = useState("");
  const [filter, setFilter] = useState<FilterType>("all");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getHistory()
      .then((data) => {
        setHistory(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const filteredHistory = history.filter((item) => {
    const matchesSearch = item.content
      .toLowerCase()
      .includes(searchTerm.toLowerCase());
    const matchesFilter =
      filter === "all" ||
      (filter === "malicious" && item.classification !== "SAFE") ||
      (filter === "safe" && item.classification === "SAFE");
    return matchesSearch && matchesFilter;
  });

  const toggleSelectItem = (id: string) => {
    setSelectedItems((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id],
    );
  };

  const toggleSelectAll = () => {
    if (selectedItems.length === filteredHistory.length) {
      setSelectedItems([]);
    } else {
      setSelectedItems(filteredHistory.map((item) => item.result_id));
    }
  };

  const deleteSelected = () => {
    setSelectedItems([]);
  };

  const exportAsCSV = () => {
    if (filteredHistory.length === 0) {
      alert("No data to export. Try adjusting your filters or search.");
      return;
    }

    // Prepare CSV headers
    const headers = [
      "Type",
      "Content",
      "Result",
      "Confidence",
      "Date & Time",
      "Status",
    ];

    // Prepare CSV rows
    const rows = filteredHistory.map((item) => [
      item.type.toUpperCase(),
      `"${item.content.replace(/"/g, '""')}"`, // Escape quotes in content
      item.classification,
      `${item.confidence_score}%`,
      new Date(item.created_at).toLocaleString(),
      item.status,
    ]);

    // Combine headers and rows
    const csvContent = [
      headers.join(","),
      ...rows.map((row) => row.join(",")),
    ].join("\n");

    // Create a blob and download
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `analysis-history-${new Date().toISOString().split("T")[0]}.csv`,
    );
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const stats = {
    total: history.length,
    malicious: history.filter((i) => i.classification !== "SAFE").length,
    safe: history.filter((i) => i.classification === "SAFE").length,
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-md p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <HistoryIcon className="size-8 text-indigo-600 mr-3" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Analysis History
              </h1>
              <p className="text-gray-600">
                View and manage your past submissions
              </p>
            </div>
          </div>
          <button
            onClick={exportAsCSV}
            className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium transition"
          >
            <Download className="size-4 mr-2" />
            Export
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <p className="text-sm text-blue-600 font-medium mb-1">
              Total Scans
            </p>
            <p className="text-3xl font-bold text-blue-900">{stats.total}</p>
          </div>
          <div className="bg-red-50 rounded-lg p-4">
            <p className="text-sm text-red-600 font-medium mb-1">
              Threats Detected
            </p>
            <p className="text-3xl font-bold text-red-900">{stats.malicious}</p>
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <p className="text-sm text-green-600 font-medium mb-1">
              Safe Items
            </p>
            <p className="text-3xl font-bold text-green-900">{stats.safe}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-md p-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 size-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search in history..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setFilter("all")}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === "all"
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter("malicious")}
              className={`flex items-center px-4 py-2 rounded-lg font-medium transition ${
                filter === "malicious"
                  ? "bg-red-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              <AlertTriangle className="size-4 mr-2" />
              Malicious
            </button>
            <button
              onClick={() => setFilter("safe")}
              className={`flex items-center px-4 py-2 rounded-lg font-medium transition ${
                filter === "safe"
                  ? "bg-green-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              <CheckCircle className="size-4 mr-2" />
              Safe
            </button>
          </div>
        </div>

        {selectedItems.length > 0 && (
          <div className="mt-4 flex items-center justify-between bg-indigo-50 border border-indigo-200 rounded-lg p-3">
            <span className="text-indigo-900 font-medium">
              {selectedItems.length} item(s) selected
            </span>
            <button
              onClick={deleteSelected}
              className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium transition"
            >
              <Trash2 className="size-4 mr-2" />
              Delete Selected
            </button>
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-4 text-left">
                  <input
                    type="checkbox"
                    checked={
                      selectedItems.length === filteredHistory.length &&
                      filteredHistory.length > 0
                    }
                    onChange={toggleSelectAll}
                    className="size-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                  />
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Content
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Result
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Confidence
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date & Time
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredHistory.map((item) => (
                <tr
                  key={item.result_id}
                  className="hover:bg-gray-50 transition"
                >
                  <td className="px-6 py-4">
                    <input
                      type="checkbox"
                      checked={selectedItems.includes(item.result_id)}
                      onChange={() => toggleSelectItem(item.result_id)}
                      className="size-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {item.type.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="max-w-md truncate text-sm text-gray-900">
                      {item.content}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        item.classification === "SAFE"
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {item.classification === "SAFE" ? (
                        <CheckCircle className="size-3 mr-1" />
                      ) : (
                        <AlertTriangle className="size-3 mr-1" />
                      )}
                      {item.classification}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {item.confidence_score}%
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(item.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.status}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {loading && (
          <div className="text-center py-12">
            <p className="text-gray-500">Loading...</p>
          </div>
        )}

        {!loading && error && (
          <div className="text-center py-12">
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {!loading && !error && filteredHistory.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No results found</p>
          </div>
        )}
      </div>
    </div>
  );
}
