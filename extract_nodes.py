import json

def extract():
    try:
        with open(r'C:\Users\Dell\Desktop\New folder\Data\temp.txt', encoding='utf-8') as f:
            data = json.load(f)
            
        def find_attr(obj, name):
            if isinstance(obj, dict):
                if obj.get('name') == name:
                    return obj
                for v in obj.values():
                    res = find_attr(v, name)
                    if res: return res
            elif isinstance(obj, list):
                for item in obj:
                    res = find_attr(item, name)
                    if res: return res
            return None

        attr = find_attr(data, 'recommended_browse_nodes')
        if not attr:
            print("Attribute not found")
            return
            
        nodes = attr.get('enumerationValues', [])
        # Format: (Group, Label, ID)
        results = []
        for n in nodes:
            desc = n.get('description', '')
            label = n.get('displayLabel', '')
            val = n.get('value', '')
            results.append({"desc": desc, "label": label, "value": val})
            
        print(json.dumps(results, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    extract()
