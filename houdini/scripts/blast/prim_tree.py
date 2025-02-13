
from pathlib import Path

FILE_TAG = '<file>'

class PrimTree():
    
    def __init__(self):
        self.tree = {}
    
    def addPath(self, path: str):
        """
        Add a path as a new branch to the tree.
        
        Args:
            path (str): A single path to add to the tree.
        """
        
        if path.startswith("/"):
            path = path[1:]
        
        parts = Path(path).parts
        
        currentLevel = self.tree
        path_length = len(parts)
        for i, part in enumerate(parts):
            if i+1 == path_length:
                if not part in currentLevel[FILE_TAG]:
                    currentLevel[FILE_TAG].append(part)
                break
            if not part in currentLevel :
                currentLevel[part] = {FILE_TAG: []}
            currentLevel = currentLevel[part]
        
    def addPaths(self, paths: list[str]):
        """
        Add all primitives from a paths list using addPath.
        
        Args:
            paths (list[str]): List of path to add to the tree.
        """
        for path in paths:
            self.addPath(path)

    def printTree(self, d, indent=0):
        """
        Print the file tree structure with proper indentation.
        """
        for key, value in d.items():
            if key == FILE_TAG:
                if value:
                    print('  ' * indent + str(value))
            else:
                print('  ' * indent + str(key))
                if isinstance(value, dict):
                    self.printTree(value, indent+1)
                else:
                    print('  ' * (indent+1) + str(value))
    
    def getPathsFromDepth(self, depth: int):
        """Get all path that are inferior to depth.

        Args:
            depth (int): Maximum depth to parse.

        Returns:
            list[str]: List of path.
        """        
        
        path_list = []
        
        def traverse(node, path, currentDepth):
            if currentDepth == depth:
                path_list.append(f"{path}/*")
                return
            
            for key, value in node.items():
                if key == FILE_TAG:
                    for v in value:
                        path_list.append(f"{path}/{v}")
                if isinstance(value, dict):
                    if key != FILE_TAG:
                        traverse(value, f"{path}/{key}", currentDepth+1)
                        
        traverse(self.tree, "", 0)
        return path_list
    
if __name__ == "__main__":
    tree = PrimTree()
    
    path_list = ["/geo/xform/aiguille",
                 "/geo/xform/test",
                 "/truc/xform/asdasd",
                 "/test/short"]
    tree.addPaths(path_list)
    tree.printTree(tree.tree)
    
    print(tree.getPathsFromDepth(3))