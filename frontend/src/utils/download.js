export function downloadAnalysis(articleText, results) {
  const exportData = {
    generated_at: new Date().toISOString(),
    application:
      "Intelligent News Article Analysis and Entity Relationship Extraction System",

    input: {
      article: articleText,
    },

    analysis: results,
  };

  const blob = new Blob(
    [JSON.stringify(exportData, null, 2)],
    {
      type: "application/json",
    }
  );

  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");

  link.href = url;

  const timestamp = new Date()
    .toISOString()
    .replace(/[:.]/g, "-");

  link.download = `news_analysis_${timestamp}.json`;

  document.body.appendChild(link);

  link.click();

  document.body.removeChild(link);

  URL.revokeObjectURL(url);
}