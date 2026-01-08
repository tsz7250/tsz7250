import os
import requests

# Configuration
USERNAME = "tsz7250"
# GH_TOKEN is injected by GitHub Actions
TOKEN = os.environ.get("GH_TOKEN")

query = """
{
  user(login: "%s") {
    lists(first: 5) {
      nodes {
        name
        description
        slug
        items(first: 5) {
          nodes {
            ... on Repository {
              name
              url
              description
              primaryLanguage {
                name
              }
            }
          }
        }
      }
    }
  }
}
""" % USERNAME

def fetch_lists():
    if not TOKEN:
        raise Exception("GH_TOKEN environment variable not set")
        
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.post("https://api.github.com/graphql", json={'query': query}, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
             raise Exception(f"GraphQL Errors: {data['errors']}")
        return data['data']['user']['lists']['nodes']
    else:
        raise Exception(f"Query failed: {response.status_code}, {response.text}")

def generate_markdown(lists):
    md = ""
    if not lists:
        return "_No public lists found._\n"

    for lst in lists:
        list_url = f"https://github.com/stars/{USERNAME}/lists/{lst['slug']}"
        md += f"### 📂 [{lst['name']}]({list_url})\n"
        if lst['description']:
            md += f"> {lst['description']}\n\n"
        
        for item in lst['items']['nodes']:
            if 'name' in item:
                # Add language badge or text if available
                lang = ""
                if item.get('primaryLanguage'):
                    lang = f" ` {item['primaryLanguage']['name']} `"
                
                md += f"- [**{item['name']}**]({item['url']}){lang}  \n"
                if item['description']:
                    md += f"  {item['description']}\n"
                md += "\n"
        md += "\n"
    return md

if __name__ == "__main__":
    try:
        lists = fetch_lists()
        new_content = generate_markdown(lists)
        
        readme_path = "README.md"
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        start_marker = "<!-- START_GITHUB_LISTS -->"
        end_marker = "<!-- END_GITHUB_LISTS -->"
        
        start_idx = content.find(start_marker) + len(start_marker)
        end_idx = content.find(end_marker)
        
        if start_idx - len(start_marker) != -1 and end_idx != -1:
            updated_content = content[:start_idx] + "\n" + new_content + content[end_idx:]
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
            print("README updated successfully.")
        else:
            print("Markers not found in README.md")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
