import { z } from "zod"

const TAVILY_API_URL = "https://api.tavily.com/search"

export default {
  description:
    "Search the web using Tavily AI. Returns real-time search results with titles, URLs, and content snippets. Use this when you need up-to-date information from the internet.",
  args: {
    query: z.string().describe("The search query"),
    max_results: z
      .number()
      .optional()
      .default(5)
      .describe("Maximum number of results to return (default: 5, max: 10)"),
    search_depth: z
      .enum(["basic", "advanced"])
      .optional()
      .default("basic")
      .describe("Search depth: 'basic' for speed, 'advanced' for thoroughness"),
  },
  async execute(args: any) {
    const apiKey = process.env.TAVILY_API_KEY
    if (!apiKey) {
      return "Error: TAVILY_API_KEY environment variable is not set."
    }

    const maxResults = Math.min(args.max_results ?? 5, 10)

    try {
      const response = await fetch(TAVILY_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          api_key: apiKey,
          query: args.query,
          max_results: maxResults,
          search_depth: args.search_depth ?? "basic",
          include_answer: true,
          include_raw_content: false,
        }),
      })

      if (!response.ok) {
        const text = await response.text()
        return `Error: Tavily API returned ${response.status}: ${text}`
      }

      const data = await response.json()

      let output = ""

      if (data.answer) {
        output += `## Answer\n\n${data.answer}\n\n`
      }

      output += `## Search Results for "${args.query}"\n\n`

      for (const result of data.results ?? []) {
        output += `### [${result.title}](${result.url})\n`
        output += `${result.content}\n\n`
      }

      return output.trim()
    } catch (err: any) {
      return `Error: Failed to search: ${err.message}`
    }
  },
}
