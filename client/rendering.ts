import morphdom from "morphdom";

export function nodeIsElement(node: Node) {
  return node.nodeType == Node.ELEMENT_NODE;
}

export function nodeIsUiNode(node: HTMLElement) {
  return !["SCRIPT", "LINK", "STYLE"].includes(node.tagName);
}

export function nodeHasFalkNodeId(node: HTMLElement) {
  return node.hasAttribute("data-falk-id");
}

export function nodeShouldBeSkipped(node: HTMLElement) {
  return node.hasAttribute("data-skip-rerendering");
}

export function getFalkNodeId(node: HTMLElement) {
  return node.getAttribute("data-falk-id");
}

export function iterFalkComponents(options: {
  rootNode: HTMLElement;
  callback: (node: HTMLElement) => any;
  skipNodes: boolean;
}) {
  let skipNode: boolean = false;

  if (options.skipNodes && !skipNode && nodeShouldBeSkipped(options.rootNode)) {
    skipNode = true;
  }

  Array.from(options.rootNode.children).forEach((child: HTMLElement) => {
    if (!nodeIsUiNode(child)) {
      return;
    }

    iterFalkComponents({
      rootNode: child,
      callback: options.callback,
      skipNodes: options.skipNodes,
    });
  });

  if (!skipNode && nodeHasFalkNodeId(options.rootNode)) {
    options.callback(options.rootNode);
  }
}

export function patchNode(options: {
  node: HTMLElement;
  newNode: HTMLElement;
  onInitialRender: (node: HTMLElement) => any;
  onRender: (node: HTMLElement) => any;
  onBeforeUnmount: (node: HTMLElement) => any;
  skipNodes: boolean;
}) {
  // patch nodes
  morphdom(options.node, options.newNode, {
    getNodeKey: (node: HTMLElement) => {
      if (!nodeIsElement(node)) {
        return;
      }

      if (options.skipNodes && nodeShouldBeSkipped(node)) {
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

      if (options.skipNodes && nodeShouldBeSkipped(fromEl)) {
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

      if (options.skipNodes && nodeShouldBeSkipped(fromEl)) {
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

      if (options.skipNodes && nodeShouldBeSkipped(node)) {
        return false;
      }

      // run onBeforeUmount hooks
      if (nodeIsUiNode(node) && nodeHasFalkNodeId(node)) {
        iterFalkComponents({
          rootNode: node,
          skipNodes: false,
          callback: options.onBeforeUnmount,
        });
      }

      return true;
    },
  });

  // run rendering hooks
  iterFalkComponents({
    rootNode: options.node,
    skipNodes: options.skipNodes,
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
