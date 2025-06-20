class Node:
    type: str
    msg: str
    next: list[Node]

class Tree:
    def __init__(self):
        self.root: list[Node] = []

    def getAll():
        pass

    def getConversation(self, conv_id: str):
        path = conv_id.split(':')
        conv = [{'role': self.root[path[0]].type, 'content': self.root[path[0]].msg}]
        curr_node: Node = self.root[path[0]]
        for step in path[1:]:
            curr_node = curr_node.next[step]
            conv.append({'role': curr_node.type, 'content': curr_node.msg})

        return conv

    def addNode(self, conv_id, type, msg):
        path = conv_id.split(':')
        curr_node: Node = self.root[path[0]]
        for step in path[1:]:
            curr_node = curr_node.next[step]
        curr_node.next.append()

        return conv_id + ':' + (len(curr_node.next) - 1)



