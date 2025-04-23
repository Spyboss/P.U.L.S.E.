"""
Improved error handling for Notion commands
"""

# Provide more helpful error messages based on the error type
if "no attribute" in error_str:
    # Method not found error
    missing_method = re.search(r"no attribute '([^']+)'", str(e))
    if missing_method:
        method_name = missing_method.group(1)
        return f"The Notion integration doesn't support the '{method_name}' operation yet. Please check the help menu for available commands."
elif "not configured" in error_str or "api key" in error_str:
    return "Notion API is not configured. Please set the NOTION_API_KEY environment variable in your .env file."
elif "401" in error_str or "unauthorized" in error_str or "authentication" in error_str:
    return "Notion authentication failed. Please check your NOTION_API_KEY in the .env file."
elif "403" in error_str or "forbidden" in error_str:
    return "Access to this Notion resource is forbidden. You may not have permission to access it."
elif "404" in error_str or "not found" in error_str:
    return "Notion resource not found. Please check that the page exists and is accessible."
elif "network" in error_str or "connection" in error_str:
    return "Network error while connecting to Notion. Please check your internet connection."
else:
    return f"Error processing Notion command: {str(e)}"
