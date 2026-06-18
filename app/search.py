import numpy as np

class BruteForceEngine:
    def __init__(self):
        # A simple flat list to hold our document dictionaries in memory
        self.nodes = []

    def add(self, name, vector, content):
        # Convert the incoming list coordinate to a NumPy array and save it
        self.nodes.append({"name": name, "vector": np.array(vector), "content": content})

    def search(self, query_vector):
        if not self.nodes: 
            return None, float('inf'), "Database Empty"
        
        q = np.array(query_vector)
        
        # Loop through every single node and pick the one with the smallest Euclidean distance
        best_node = min(self.nodes, key=lambda n: np.linalg.norm(n["vector"] - q))
        dist = float(np.linalg.norm(best_node["vector"] - q))
        
        return best_node["name"], dist, best_node["content"]


class KDNode:
    # A helper class that acts as a single branch/leaf point inside the KD-Tree
    def __init__(self, item, left=None, right=None):
        self.item = item
        self.left = left
        self.right = right


class KDTreeEngine:
    def __init__(self):
        self.root = None

    def build(self, items, depth=0):
        if not items: 
            return None
            
        k = len(items[0]["vector"])
        axis = depth % k  # Alternates: Depth 0 splits on X-axis, Depth 1 splits on Y-axis
        
        # Sort items by the current axis and find the median point to split space
        items.sort(key=lambda x: x["vector"][axis])
        median = len(items) // 2
        
        # Recursively build the left side and right side of the spatial tree
        return KDNode(
            item=items[median],
            left=self.build(items[:median], depth + 1),
            right=self.build(items[median + 1:], depth + 1)
        )

    def search(self, query_vector):
        if not self.root: 
            return None, float('inf'), "Database Empty"
        
        best = {"node": None, "dist": float('inf')}
        q = np.array(query_vector)
        
        def traverse(node, depth=0):
            if not node: 
                return
                
            # Calculate distance from current node to our query point
            dist = np.linalg.norm(node.item["vector"] - q)
            if dist < best["dist"]:
                best["dist"] = dist
                best["node"] = node.item
            
            axis = depth % len(query_vector)
            
            # Decide which side of the tree branch to step down first
            next_branch = node.left if query_vector[axis] < node.item["vector"][axis] else node.right
            opposite_branch = node.right if next_branch == node.left else node.left
            
            traverse(next_branch, depth + 1)
            
            # Hyperplane check: If the opposite branch could contain a closer point, check it too
            if abs(query_vector[axis] - node.item["vector"][axis]) < best["dist"]:
                traverse(opposite_branch, depth + 1)

        traverse(self.root)
        return best["node"]["name"], float(best["dist"]), best["node"]["content"]