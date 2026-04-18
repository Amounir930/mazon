import json

with open(r"C:\Users\Dell\Desktop\learn\amazon\Data\temp.txt", "r", encoding="utf-8") as f:
    data = json.load(f)

# Navigate to metadata menus
menus = data["listing"]["metadata"]["menus"]
print(f"Total menus: {len(menus)}")

for menu_idx, menu in enumerate(menus):
    groups = menu.get("attributeGroups", [])
    print(f"\nMenu {menu_idx}: {len(groups)} attribute groups")
    
    for g_idx, group in enumerate(groups):
        group_name = group.get("name", "unknown")
        attrs = group.get("attributes", [])
        
        required_attrs = []
        for attr in attrs:
            if attr.get("usage") == "REQUIRED":
                required_attrs.append({
                    "name": attr["name"],
                    "datatype": attr.get("datatype"),
                    "label": attr.get("displayLabel", ""),
                })
        
        if required_attrs:
            print(f"\n  Group '{group_name}': {len(required_attrs)} REQUIRED fields")
            for attr in required_attrs:
                print(f"    - {attr['name']:55s} | {attr['datatype']:8s} | {attr['label']}")
