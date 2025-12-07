/**
 * CV Preview Component
 * Compact CV preview for sidebar display
 */
import { useState } from "react";
import { Eye, EyeOff, User, Briefcase, GraduationCap, Award, Mail, Phone, MapPin } from "lucide-react";

export default function CVPreview({ cvData }) {
  const [expanded, setExpanded] = useState(false);

  if (!cvData) return null;

  // Extract data from cvData - handle both direct and json_content structure
  const personalInfo = cvData.personal_info || cvData.json_content?.personal_info || {};
  const education = cvData.education || cvData.json_content?.education || [];
  const workExperience = cvData.work_experience || cvData.json_content?.work_experience || [];
  const skills = cvData.personal_skills || cvData.json_content?.personal_skills || {};
  const summary = cvData.summary || cvData.json_content?.summary || "";
  
  // Get name
  const fullName = personalInfo.full_name || 
                   `${personalInfo.first_name || ""} ${personalInfo.surname || ""}`.trim() ||
                   "Your Name";
  
  const email = personalInfo.email || "";
  const phone = personalInfo.phone || personalInfo.mobile || "";
  const location = personalInfo.location || personalInfo.address || "";

  // Extract skills
  const jobSkills = skills.job_related_skills || skills.technical_skills || [];
  const computerSkills = skills.computer_skills || skills.programming_skills || [];
  const languages = skills.languages || [];

  return (
    <div className="border-t border-gray-200 mt-4 pt-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-2 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
      >
        <div className="flex items-center gap-2">
          {expanded ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          <span>CV Preview</span>
        </div>
        <span className="text-xs text-gray-500">{expanded ? "Hide" : "Show"}</span>
      </button>

      {expanded && (
        <div className="mt-3 bg-white border border-gray-200 rounded-lg p-4 max-h-[600px] overflow-y-auto text-xs">
          <div className="cv-preview">
            {/* Header */}
            <div className="border-b border-gray-300 pb-3 mb-3">
              <h1 className="text-lg font-bold text-gray-900 mb-1">{fullName}</h1>
              <div className="flex flex-col gap-1 text-gray-600">
                {email && (
                  <div className="flex items-center gap-1">
                    <Mail className="w-3 h-3" />
                    <span>{email}</span>
                  </div>
                )}
                {phone && (
                  <div className="flex items-center gap-1">
                    <Phone className="w-3 h-3" />
                    <span>{phone}</span>
                  </div>
                )}
                {location && (
                  <div className="flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    <span>{location}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Summary */}
            {summary && (
              <div className="mb-4">
                <h2 className="text-sm font-bold text-gray-800 mb-1 flex items-center gap-1">
                  <User className="w-3 h-3" />
                  Summary
                </h2>
                <p className="text-gray-700 text-xs leading-relaxed">{summary}</p>
              </div>
            )}

            {/* Work Experience */}
            {workExperience && workExperience.length > 0 && (
              <div className="mb-4">
                <h2 className="text-sm font-bold text-gray-800 mb-2 flex items-center gap-1">
                  <Briefcase className="w-3 h-3" />
                  Experience
                </h2>
                {workExperience.slice(0, 3).map((exp, idx) => (
                  <div key={idx} className="mb-2 pb-2 border-b border-gray-100 last:border-0">
                    <div className="font-semibold text-gray-900">{exp.job_title || "Position"}</div>
                    <div className="text-gray-600">{exp.company || "Company"}</div>
                    {(exp.start_date || exp.end_date) && (
                      <div className="text-gray-500 text-xs">
                        {exp.start_date || ""} - {exp.end_date || "Present"}
                      </div>
                    )}
                    {exp.description && (
                      <p className="text-gray-700 text-xs mt-1 line-clamp-2">{exp.description}</p>
                    )}
                  </div>
                ))}
                {workExperience.length > 3 && (
                  <p className="text-xs text-gray-500 italic">+{workExperience.length - 3} more</p>
                )}
              </div>
            )}

            {/* Education */}
            {education && education.length > 0 && (
              <div className="mb-4">
                <h2 className="text-sm font-bold text-gray-800 mb-2 flex items-center gap-1">
                  <GraduationCap className="w-3 h-3" />
                  Education
                </h2>
                {education.slice(0, 2).map((edu, idx) => (
                  <div key={idx} className="mb-2 pb-2 border-b border-gray-100 last:border-0">
                    <div className="font-semibold text-gray-900">
                      {edu.degree || edu.qualification || "Degree"}
                    </div>
                    <div className="text-gray-600">{edu.institution || edu.school || "Institution"}</div>
                    {edu.field_of_study && (
                      <div className="text-gray-600 text-xs">{edu.field_of_study}</div>
                    )}
                    {edu.graduation_year && (
                      <div className="text-gray-500 text-xs">{edu.graduation_year}</div>
                    )}
                  </div>
                ))}
                {education.length > 2 && (
                  <p className="text-xs text-gray-500 italic">+{education.length - 2} more</p>
                )}
              </div>
            )}

            {/* Skills */}
            {(jobSkills.length > 0 || computerSkills.length > 0 || languages.length > 0) && (
              <div className="mb-4">
                <h2 className="text-sm font-bold text-gray-800 mb-2 flex items-center gap-1">
                  <Award className="w-3 h-3" />
                  Skills
                </h2>
                {jobSkills.length > 0 && (
                  <div className="mb-2">
                    <div className="text-gray-600 text-xs mb-1">Job Skills:</div>
                    <div className="flex flex-wrap gap-1">
                      {jobSkills.slice(0, 6).map((skill, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs"
                        >
                          {skill}
                        </span>
                      ))}
                      {jobSkills.length > 6 && (
                        <span className="px-2 py-0.5 text-gray-500 text-xs">
                          +{jobSkills.length - 6}
                        </span>
                      )}
                    </div>
                  </div>
                )}
                {computerSkills.length > 0 && (
                  <div className="mb-2">
                    <div className="text-gray-600 text-xs mb-1">Technical:</div>
                    <div className="flex flex-wrap gap-1">
                      {computerSkills.slice(0, 6).map((skill, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 bg-green-50 text-green-700 rounded text-xs"
                        >
                          {skill}
                        </span>
                      ))}
                      {computerSkills.length > 6 && (
                        <span className="px-2 py-0.5 text-gray-500 text-xs">
                          +{computerSkills.length - 6}
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

