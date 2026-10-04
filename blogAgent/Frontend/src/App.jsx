import React, { useState } from "react";

function App() {
  const [topic, setTopic] = useState("");
  const [currentStep, setCurrentStep] = useState(0);
  const [draft, setDraft] = useState("");
  const [evaluation, setEvaluation] = useState("");
  const [publishDetails, setPublishDetails] = useState(null);
  const [logs, setLogs] = useState([]);
  const [logsOpen, setLogsOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  // Agent command
  const [agentCommand, setAgentCommand] = useState("");
  const [agentResponse, setAgentResponse] = useState("");
  const [isAgentRunning, setIsAgentRunning] = useState(false);

  // Approval Modal States
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [approvalMode, setApprovalMode] = useState("initial");
  const [feedback, setFeedback] = useState("");
  const [includeImage, setIncludeImage] = useState(false);

  const steps = [
    "Topic Received",
    "Writing Draft",
    "Awaiting Approval",
    "Publishing",
    "Completed",
  ];

  const log = (msg) =>
    setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);

  // ------------------------------------------
  // 1. Generate Draft
  // ------------------------------------------
  const generateDraft = async () => {
    if (!topic.trim()) return;

    setIsGenerating(true);
    setCurrentStep(0);
    setDraft("");
    setEvaluation("");
    setPublishDetails(null);
    setLogs([]);
    setFeedback("");
    setApprovalMode("initial");

    log("Sending request to backend...");
    setCurrentStep(1);

    try {
      const response = await fetch("http://127.0.0.1:8000/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: topic,
          include_image: includeImage,
        }),
      });

      const data = await response.json();
      log("Draft received from backend.");

      setCurrentStep(2);
      setDraft(data.draft || "No draft returned.");
      setEvaluation(data.evaluation || "");

      setShowApprovalModal(true);
      setIsGenerating(false);
    } catch (err) {
      log("Error: " + err.message);
      setIsGenerating(false);
    }
  };

  // ------------------------------------------
  // 2. Refine Draft
  // ------------------------------------------
  const refineDraft = async () => {
    if (!feedback.trim()) {
      alert("Please provide feedback for refinement.");
      return;
    }

    setShowApprovalModal(false);
    setIsGenerating(true);
    log("Refining draft based on feedback...");
    setCurrentStep(1);

    try {
      const response = await fetch("http://127.0.0.1:8000/refine", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          original_topic: topic,
          feedback: feedback,
          previous_draft: draft,
          include_image: includeImage,
        }),
      });

      const data = await response.json();
      log("Refined draft received.");

      setCurrentStep(2);
      setDraft(data.draft || "No draft returned.");
      setEvaluation(data.evaluation || "");
      setFeedback("");
      setApprovalMode("refined");

      setShowApprovalModal(true);
      setIsGenerating(false);
    } catch (err) {
      log("Error: " + err.message);
      setIsGenerating(false);
    }
  };

  // ------------------------------------------
  // 3. Publish Draft
  // ------------------------------------------
  const approveAndPublish = async () => {
    setShowApprovalModal(false);
    setCurrentStep(3);
    log("Publishing approved draft...");

    try {
      const response = await fetch("http://127.0.0.1:8000/publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: topic,
          content: draft,
          include_image: includeImage,
        }),
      });

      const data = await response.json();
      log("Post published successfully.");

      setPublishDetails({
        title: topic,
        postId: data.result?.postId || "AUTO_ID",
        url: data.result?.url || "https://alok12blogger.blogspot.com",
      });

      setCurrentStep(4);
    } catch (err) {
      log("Publish error: " + err.message);
    }
  };

  const rejectDraft = () => {
    setShowApprovalModal(false);
    log("Draft rejected by user.");
    setCurrentStep(0);
  };

  // ------------------------------------------
  // 4. Agent Command Handler
  // ------------------------------------------
  const runAgentCommand = async () => {
    if (!agentCommand.trim()) return;

    setIsAgentRunning(true);
    log("Sending command to agent...");

    try {
      const response = await fetch("http://127.0.0.1:8000/agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: agentCommand }),
      });

      const data = await response.json();
      setAgentResponse(data.response || "No response from agent.");
      log("Agent responded.");
    } catch (err) {
      log("Agent error: " + err.message);
      setAgentResponse("Error: " + err.message);
    }

    setIsAgentRunning(false);
  };

  // ------------------------------------------
  // UI Layout
  // ------------------------------------------
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="px-6 py-5">
          <h1 className="text-xl font-semibold text-gray-900">
            Blog Writer & Agent Dashboard
          </h1>
        </div>
      </header>

      {/* --------------------- Approval Modal --------------------- */}
      {showApprovalModal && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-xl shadow-lg w-full max-w-2xl max-h-screen overflow-y-auto">
            <div className="flex items-start gap-3 mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                Review Your Blog Draft
              </h2>
            </div>

            <div className="bg-gray-50 border rounded-lg p-4 mb-4 max-h-64 overflow-y-auto">
              <h3 className="text-sm font-medium text-gray-700 mb-2">
                Draft Preview:
              </h3>
              <div className="text-sm whitespace-pre-wrap">{draft}</div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Provide Feedback (optional):
              </label>
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                className="w-full h-24 px-3 py-2 border rounded-lg text-sm resize-none"
                placeholder="Make it more technical, add examples..."
              />
            </div>

            <div className="flex flex-col sm:flex-row justify-end gap-3">
              <button
                onClick={rejectDraft}
                className="px-4 py-2 bg-gray-200 rounded-lg"
              >
                Reject
              </button>

              <button
                onClick={refineDraft}
                disabled={!feedback.trim()}
                className="px-4 py-2 bg-yellow-600 text-white rounded-lg disabled:opacity-40"
              >
                Refine with Feedback
              </button>

              <button
                onClick={approveAndPublish}
                className="px-4 py-2 bg-green-600 text-white rounded-lg"
              >
                Approve & Publish
              </button>
            </div>
          </div>
        </div>
      )}

      {/* --------------------- MAIN LAYOUT --------------------- */}
      <div className="flex-1 flex flex-col lg:flex-row">
        {/* --------------------- LEFT SIDEBAR --------------------- */}
        <div className="w-full lg:w-96 bg-gray-50 border-r border-gray-200 p-6 overflow-y-auto">
          <div className="bg-white rounded-xl p-5 shadow-sm mb-6">
            <label className="block text-sm font-medium mb-2">Blog Topic</label>

            <textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full h-24 px-3 py-2 border rounded-lg"
              placeholder="Enter your blog topic..."
            />

            <div className="mt-4 flex items-center gap-2">
              <input
                type="checkbox"
                id="includeImage"
                checked={includeImage}
                onChange={(e) => setIncludeImage(e.target.checked)}
                className="w-4 h-4"
              />
              <label className="text-sm">Include featured image</label>
            </div>

            <button
              onClick={generateDraft}
              disabled={isGenerating || !topic.trim()}
              className="w-full mt-4 h-11 bg-blue-600 text-white rounded-lg disabled:opacity-50"
            >
              {isGenerating ? "Generating..." : "Generate Blog Draft"}
            </button>
          </div>

          {/* Workflow Steps */}
          <div>
            <h2 className="text-base font-medium mb-3">Workflow Status</h2>
            <div className="space-y-4">
              {steps.map((step, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center ${
                      i < currentStep
                        ? "bg-blue-600 text-white"
                        : i === currentStep
                        ? "bg-blue-600 text-white animate-pulse"
                        : "bg-gray-300 text-gray-600"
                    }`}
                  >
                    {i < currentStep ? "✓" : i + 1}
                  </div>
                  <span
                    className={`text-sm ${
                      i <= currentStep ? "text-gray-900" : "text-gray-500"
                    }`}
                  >
                    {step}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* --------------------- RIGHT CONTENT AREA --------------------- */}
        <div className="flex-1 p-6 overflow-y-auto">
          {/* Draft Preview */}
          <div className="bg-white p-5 rounded-xl shadow-sm mb-6">
            <h2 className="text-lg font-semibold mb-4">Draft Preview</h2>
            <div className="min-h-64 border rounded-lg p-4 whitespace-pre-wrap">
              {draft || "Draft will appear here..."}
            </div>
          </div>

          {/* Status */}
          {evaluation && (
            <div className="bg-white p-5 rounded-xl shadow-sm mb-6">
              <h2 className="text-lg font-semibold mb-4">Status</h2>
              <div className="p-4 bg-blue-50 border rounded-lg">
                {evaluation}
              </div>
            </div>
          )}

          {/* Publish Details */}
          {publishDetails && (
            <div className="bg-white p-5 rounded-xl shadow-sm mb-6">
              <h2 className="text-lg font-semibold mb-4 text-green-600">
                ✓ Published Successfully
              </h2>

              <div className="space-y-3">
                <div>
                  <span className="text-sm font-medium">Post Title:</span>
                  <p>{publishDetails.title}</p>
                </div>

                <div>
                  <span className="text-sm font-medium">Post ID:</span>
                  <p className="font-mono">{publishDetails.postId}</p>
                </div>

                <div>
                  <span className="text-sm font-medium">Published URL:</span>
                  <a
                    href={publishDetails.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 underline"
                  >
                    {publishDetails.url}
                  </a>
                </div>
              </div>
            </div>
          )}

          {/* --------------------- AGENT COMMAND PANEL --------------------- */}
          <div className="bg-white p-5 rounded-xl shadow-sm mb-6">
            <h2 className="text-lg font-semibold mb-4">Agent Commands</h2>

            <textarea
              value={agentCommand}
              onChange={(e) => setAgentCommand(e.target.value)}
              placeholder="e.g., delete the recent post, list posts, update last post..."
              className="w-full h-20 px-3 py-2 border rounded-lg text-sm resize-none"
            />

            <button
              onClick={runAgentCommand}
              disabled={isAgentRunning || !agentCommand.trim()}
              className="w-full mt-3 h-11 bg-purple-600 text-white rounded-lg disabled:opacity-50"
            >
              {isAgentRunning ? "Running..." : "Run Command"}
            </button>

            {agentResponse && (
              <div className="mt-4 p-4 bg-gray-50 border rounded-lg whitespace-pre-wrap text-sm">
                <strong>Agent Response:</strong>
                <br />
                {agentResponse}
              </div>
            )}
          </div>

          {/* System Logs */}
          {logs.length > 0 && (
            <div className="bg-gray-100 rounded-lg">
              <button
                onClick={() => setLogsOpen(!logsOpen)}
                className="w-full px-5 py-3 flex justify-between items-center hover:bg-gray-200 rounded-lg"
              >
                <span className="font-medium">System Logs</span>
                <span>{logsOpen ? "▲" : "▼"}</span>
              </button>

              {logsOpen && (
                <div className="bg-white border-t p-4 max-h-64 overflow-y-auto">
                  <pre className="text-xs font-mono whitespace-pre-wrap">
                    {logs.join("\n")}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
