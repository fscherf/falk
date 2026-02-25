  public dispatchRenderEvents = (
    rootNode: HTMLElement = document.body,
    options: { initial: boolean } = { initial: false },
  ) => {
    const nodeShouldBeSkipped = (rootNode: HTMLElement, node: HTMLElement) => {
      let _node: HTMLElement = node;

      while (_node && _node != rootNode) {
        // local rendering flag
        if (_node.hasAttribute("data-skip-rerendering")) {
          return true;
        }

        _node = _node.parentElement;
      }

      return false;
    };

    iterNodes(
      "[data-falk-id]",
      (node: HTMLElement) => {
        // skip styles and scripts
        if (["SCRIPT", "LINK", "STYLE"].includes(node.tagName)) {
          return true;
        }

        // If we are not in the global init, we need to skip components that
        // are inside elements with the `data-skip-rerendering` because we
        // know that we left the out while rerendering.
        if (!options.initial) {
          if (nodeShouldBeSkipped(rootNode, node)) {
            return;
          }
        }

        if (options.initial || node != rootNode) {
          this.dispatchEvent("initialrender", node);
        }

        this.dispatchEvent("render", node);
      },
      rootNode,
    );
  };


  // node patching
  private patchNode = (node, newNode, eventType, flags) => {
    const nodeShouldBeSkipped = (node) => {
      if (flags.forceRendering) {
        return false;
      }

      if (flags.skipRendering) {
        return true;
      }

      return node.hasAttribute("data-skip-rerendering");
    };

    return morphdom(node, newNode, {
      getNodeKey: (node: HTMLElement) => {
        // use `data-falk-id` as node key
        //
        // When a view decides to unmount a component and render another
        // component with a similar markup in its place, morphdom can decide
        // to update the first component until its markup matches the
        // second component.
        // This is pretty efficient but without morphdom properly discarding
        // the components `onbeforeunmount` hooks don't work.

        // ignore non-element nodes
        if (node.nodeType !== Node.ELEMENT_NODE) {
          return false;
        }

        // ignore styles and scripts
        if (["SCRIPT", "LINK", "STYLE"].includes(node.tagName)) {
          return false;
        }

        // use `data-falk-id` as node key
        if (node.hasAttribute("data-falk-id")) {
          return node.getAttribute("data-falk-id");
        }

        // fall back to `node.id`
        return node.id;
      },

      onBeforeNodeAdded: (node) => {
        if (node.nodeType !== Node.ELEMENT_NODE) {
          return node;
        }

        const tagName: string = (node as HTMLElement).tagName;

        if (["SCRIPT", "LINK", "STYLE"].includes(tagName)) {
          return false;
        }

        if (nodeShouldBeSkipped(node)) {
          return node;
        }

        return node;
      },

      onBeforeNodeDiscarded: (node) => {
        if (node.nodeType !== Node.ELEMENT_NODE) {
          return true;
        }

        // ignore styles and scripts
        const tagName: string = (node as HTMLElement).tagName;

        if (["SCRIPT", "LINK", "STYLE"].includes(tagName)) {
          return false;
        }

        // rendering flags
        if (nodeShouldBeSkipped(node)) {
          return false;
        }

        // components
        iterNodes(
          "[data-falk-id]",
          (_node) => {
            // run beforeunmount hook
            this.dispatchEvent("beforeunmount", _node);

            // remove token from `falk.tokens`
            const nodeId = _node.getAttribute("data-falk-id");

            if (nodeId) {
              delete this.tokens[nodeId];
            }
          },
          node as HTMLElement,
        );

        return true;
      },

      onBeforeElUpdated: (fromEl, toEl) => {
        if (nodeShouldBeSkipped(fromEl)) {
          return false;
        }

        // ignore styles and scripts
        if (["SCRIPT", "LINK", "STYLE"].includes(fromEl.tagName)) {
          return false;
        }

        // Preserve values of input elements if the original event is no
        // `submit` event.
        // Normally, we don't want to override user input from the backend
        // because this almost always results in bad user experience, but when
        // submitting a form, the expected behavior is that the form
        // clears afterwards.
        // To make the backend code able to render an empty form after a
        // successful submit, or containing the submitted values in case of an
        // error, we take the new form as is and discard local values.
        if (
          eventType != "submit" &&
          ((fromEl instanceof HTMLInputElement &&
            toEl instanceof HTMLInputElement) ||
            (fromEl instanceof HTMLTextAreaElement &&
              toEl instanceof HTMLTextAreaElement) ||
            (fromEl instanceof HTMLSelectElement &&
              toEl instanceof HTMLSelectElement))
        ) {
          toEl.value = fromEl.value;
        }

        return true;
      },
    });
  };

  private patchNodeAttributes = (node, newNode) => {
    return morphdom(node, newNode, {
      onBeforeElChildrenUpdated: (fromEl, toEl) => {
        // ignore all children
        return false;
      },
    });
  };
