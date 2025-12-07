/**
 * CV Suggestions Component
 * Displays AI-powered suggestions for improving CV content
 */
import { useState } from "react";
import { Lightbulb, CheckCircle, X } from "lucide-react";

export default function CVSuggestions({ suggestions, onApply, onDismiss }) {
  if (!suggestions || Object.keys(suggestions).length === 0) {
    return null;
  }

  return (
    <div className="cv-suggestions bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
      <div className="flex items-center mb-3">
        <Lightbulb className="w-5 h-5 text-blue-600 mr-2" />
        <h3 className="font-semibold text-blue-900">AI Suggestions</h3>
      </div>
      
      {suggestions.improvements?.map((improvement, index) => (
        <div key={index} className="mb-2 p-2 bg-white rounded">
          <p className="text-sm">
            <span className="line-through text-gray-500">{improvement.weak}</span>
            {" → "}
            <span className="font-semibold text-green-600">{improvement.strong}</span>
          </p>
          <button
            onClick={() => onApply(improvement)}
            className="text-xs text-blue-600 hover:underline mt-1"
          >
            Apply suggestion
          </button>
        </div>
      ))}
      
      {suggestions.recommendations?.map((rec, index) => (
        <div key={index} className="mb-2 text-sm text-gray-700">
          <CheckCircle className="w-4 h-4 inline mr-2 text-green-600" />
          {rec}
        </div>
      ))}
    </div>
  );
}

