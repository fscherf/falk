import morphdom from "morphdom";

export function nodeIsElement(node: Node) {
  return node.nodeType == Node.ELEMENT_NODE;
}

export function nodeIsUiNode(node: HTMLElement) {
  return !["SCRIPT", "LINK", "STYLE"].includes(node.tagName);
}

export function nodeHasFalkNodeId(node: HTMLElement) {
  return node.hasAttribute("fx-id");
}

export function nodeShouldBePreserved(node: HTMLElement) {
  return node.hasAttribute("fx-preserve");
}

export function getFalkNodeId(node: HTMLElement) {
  return node.getAttribute("fx-id");
}

export function iterFalkComponents(options: {
  rootNode: HTMLElement;
  callback: (node: HTMLElement) => any;
  preserveNodes: boolean;
}) {
  let preserveNode: boolean = false;

  if (
    options.preserveNodes &&
    !preserveNode &&
    nodeShouldBePreserved(options.rootNode)
  ) {
    preserveNode = true;
  }

  Array.from(options.rootNode.children).forEach((child: HTMLElement) => {
    if (!nodeIsUiNode(child)) {
      return;
    }

    iterFalkComponents({
      rootNode: child,
      callback: options.callback,
      preserveNodes: options.preserveNodes,
    });
  });

  if (!preserveNode && nodeHasFalkNodeId(options.rootNode)) {
    options.callback(options.rootNode);
  }
}

export function patchNode(options: {
  node: HTMLElement;
  newNode: HTMLElement;
  onInitialRender: (node: HTMLElement) => any;
  onRender: (node: HTMLElement) => any;
  onBeforeUnmount: (node: HTMLElement) => any;
  preserveNodes: boolean;
}) {
  // patch nodes
  morphdom(options.node, options.newNode, {
    getNodeKey: (node: HTMLElement) => {
      if (!nodeIsElement(node)) {
        return;
      }

      if (options.preserveNodes && nodeShouldBePreserved(node)) {
        return node.id;
      }

      if (nodeHasFalkNodeId(node)) {
        return getFalkNodeId(node);
      }

      return node.id;
    },

    onBeforeElUpdated: (fromEl: HTMLElement, toEl: HTMLElement) => {
      if (!nodeIsUiNode(fromEl)) {
        return false;
      }

      if (!nodeIsElement(fromEl)) {
        return true;
      }

      if (options.preserveNodes && nodeShouldBePreserved(fromEl)) {
        return false;
      }

      return true;
    },

    onBeforeElChildrenUpdated: (fromEl: HTMLElement, toEl: HTMLElement) => {
      if (!nodeIsUiNode(fromEl)) {
        return false;
      }

      if (!nodeIsElement(fromEl)) {
        return true;
      }

      if (options.preserveNodes && nodeShouldBePreserved(fromEl)) {
        return false;
      }

      return true;
    },

    onBeforeNodeAdded: (node: HTMLElement) => {
      if (!nodeIsUiNode(node)) {
        return false;
      }

      return node;
    },

    onBeforeNodeDiscarded: (node: HTMLElement) => {
      if (!nodeIsUiNode(node)) {
        return false;
      }

      if (!nodeIsElement(node)) {
        return true;
      }

      if (options.preserveNodes && nodeShouldBePreserved(node)) {
        return false;
      }

      // run onBeforeUmount hooks
      if (nodeIsUiNode(node) && nodeHasFalkNodeId(node)) {
        iterFalkComponents({
          rootNode: node,
          preserveNodes: false,
          callback: options.onBeforeUnmount,
        });
      }

      return true;
    },
  });

  // run rendering hooks
  iterFalkComponents({
    rootNode: options.node,
    preserveNodes: options.preserveNodes,
    callback: (node: HTMLElement) => {
      if (node != options.node) {
        options.onInitialRender(node);
      }

      options.onRender(node);
    },
  });
}

export function patchNodeAttributes(options: {
  node: HTMLElement;
  newNode: HTMLElement;
  onRender: (node: HTMLElement) => any;
}) {
  // patch node
  morphdom(options.node, options.newNode, {
    onBeforeElChildrenUpdated: (fromEl: HTMLElement, toEl: HTMLElement) => {
      // ignore all children
      return false;
    },
  });

  // run rendering hooks
  options.onRender(options.node);
}
