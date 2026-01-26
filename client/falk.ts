import { WebsocketTransport } from "./websocket-transport";
import { HTTPTransport } from "./http-transport";
import { dumpEvent } from "./events";
import morphdom from "morphdom";

class Falk {
  public httpTransport: HTTPTransport;
  public websocketTransport: WebsocketTransport;

  public init = async () => {
    // setup transports
    this.httpTransport = new HTTPTransport();
    this.websocketTransport = new WebsocketTransport();

    const _init = async () => {
      // run beforeinit event handler
      this.dispatchEvent("beforeinit", document.querySelector("html"));

      // try to connect websocket
      await this.websocketTransport.init();

      // dispatch initialRender events
      this.dispatchRenderEvents(document.body, {
        initial: true,
      });
    };

    if (document.readyState === "complete") {
      await _init();
    } else {
      window.addEventListener("load", async () => {
        await _init();
      });
    }
  };

  // helper
  public parseDelay = (delay: string | number) => {
    if (typeof delay === "number") {
      return delay * 1000;
    }

    delay = delay as string;

    const match = /^(\d+(?:\.\d+)?)(ms|s|m|h)?$/.exec(delay.trim());

    if (!match) {
      throw new Error("Invalid time format: " + delay);
    }

    const value = parseFloat(match[1]);
    const unit = match[2] || "s";

    if (unit === "ms") {
      return value;
    } else if (unit === "s") {
      return value * 1000;
    } else if (unit === "m") {
      return value * 60 * 1000;
    } else if (unit === "h") {
      return value * 60 * 60 * 1000;
    } else {
      throw new Error("Unknown unit: " + unit);
    }
  };

  // events
  public iterNodes = (
    selector: string,
    callback: (node: Element) => any,
    rootNode: Element = document.body,
  ) => {
    if (rootNode.nodeType !== Node.ELEMENT_NODE) {
      return;
    }

    Array.from(rootNode.children).forEach((child) => {
      this.iterNodes(selector, callback, child);
    });

    if (rootNode.matches(selector)) {
      callback(rootNode);
    }
  };

  public dispatchEvent = (shortName: string, element: Element) => {
    const attributeName: string = `on${shortName}`;
    const eventName: string = `falk:${shortName}`;
    const attribute = element.getAttribute(attributeName);
    const fn: Function = new Function("event", attribute);

    const event = new CustomEvent(eventName, {
      bubbles: true,
      cancelable: true,
    });

    // inline event handler
    try {
      fn.call(element, event);
    } catch (error) {
      console.error(error);
    }

    // event listener
    element.dispatchEvent(event);
  };

  public dispatchRenderEvents = (
    rootNode: Element = document.body,
    options: { initial: boolean } = { initial: false },
  ) => {
    this.iterNodes(
      "[data-falk-id]",
      (node) => {
        if (options.initial || node != rootNode) {
          this.dispatchEvent("initialrender", node);
        }

        this.dispatchEvent("render", node);
      },
      rootNode,
    );
  };

  // node patching
  public patchNode = (node, newNode, eventType, flags) => {
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
      onBeforeNodeAdded: (node) => {
        // ignore styles and scripts
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
        // ignore styles and scripts
        if (node.nodeType !== Node.ELEMENT_NODE) {
          return true;
        }

        const tagName: string = (node as HTMLElement).tagName;

        if (["SCRIPT", "LINK", "STYLE"].includes(tagName)) {
          return false;
        }

        if (nodeShouldBeSkipped(node)) {
          return false;
        }

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

  public patchNodeAttributes = (node, newNode) => {
    return morphdom(node, newNode, {
      onBeforeElChildrenUpdated: (fromEl, toEl) => {
        // ignore all children
        return false;
      },
    });
  };

  // callbacks
  public runCallback = async (options: {
    optionsString?: string;
    event?: Event;
    node?: HTMLElement;
    nodeId?: string;
    selector?: string;
    callbackName?: string;
    callbackArgs?: any;
    stopEvent?: boolean;
    delay?: string | number;
  }) => {
    let nodes: Array<HTMLElement>;

    // parse options string
    if (options.optionsString) {
      const optionsOverrides = JSON.parse(
        decodeURIComponent(options.optionsString),
      );

      options = Object.assign(options, optionsOverrides);
    }

    // find event type
    let eventType: string = "";

    if (event) {
      eventType = event.type;
    }

    // find nodes
    if (options.node) {
      nodes = [options.node];
    } else if (options.nodeId) {
      const node: HTMLElement = document.querySelector(
        `[data-falk-id=${options.nodeId}]`,
      );

      if (!node) {
        throw `no node with id ${options.nodeId}`;
      }

      nodes = [node];
    } else if (options.selector) {
      nodes = Array.from(document.querySelectorAll(options.selector));
    }

    // iter nodes
    for (const node of nodes) {
      const eventData = dumpEvent(options.event);
      const nodeId = node.getAttribute("data-falk-id");
      const token = node.getAttribute("data-falk-token");
      const callbackName = options.callbackName || "";
      const callbackArgs = options.callbackArgs || {};

      // The event is `undefined` when handling non-standard event handler
      // like `onRender`.
      if (options.event && options.stopEvent) {
        options.event.stopPropagation();
        options.event.preventDefault();
      }

      setTimeout(
        async () => {
          // run beforerequest hook
          this.dispatchEvent("beforerequest", node);

          // send mutation request
          let responseData;

          // HTTP multipart POST (file uploads)
          if (eventData.files.length > 0) {
            responseData =
              await this.httpTransport.sendMultipartMutationRequest({
                nodeId: nodeId,
                token: token,
                callbackName: callbackName,
                callbackArgs: callbackArgs,
                eventData: eventData,
              });

            // websocket
          } else if (this.websocketTransport.available) {
            responseData = await this.websocketTransport.sendMutationRequest({
              nodeId: nodeId,
              token: token,
              callbackName: callbackName,
              callbackArgs: callbackArgs,
              eventData: eventData,
            });

            // HTTP POST
          } else {
            responseData = await this.httpTransport.sendMutationRequest({
              nodeId: nodeId,
              token: token,
              callbackName: callbackName,
              callbackArgs: callbackArgs,
              eventData: eventData,
            });
          }

          // parse response HTML
          const domParser = new DOMParser();

          const newDocument = domParser.parseFromString(
            responseData.body as string,
            "text/html",
          );

          // load linked styles
          const linkNodes = newDocument.head.querySelectorAll(
            "link[rel=stylesheet]",
          );

          linkNodes.forEach((node) => {
            // check if style is already loaded
            let selector: string;
            const styleHref: string = node.getAttribute("href");

            if (styleHref) {
              selector = `link[href="${styleHref}"]`;
            } else {
              const styleId: string = node.getAttribute("data-falk-id");

              selector = `link[data-falk-id="${styleId}"]`;
            }

            if (document.querySelector(selector)) {
              return;
            }

            // load style
            document.head.appendChild(node);
          });

          // load styles
          const styleNodes = newDocument.head.querySelectorAll("style");

          styleNodes.forEach((node) => {
            // check if style is already loaded
            const styleId: string = node.getAttribute("data-falk-id");
            const selector = `style[data-falk-id="${styleId}"]`;

            if (document.querySelector(selector)) {
              return;
            }

            // load style
            document.head.appendChild(node);
          });

          // load scripts
          const scriptNodes = newDocument.body.querySelectorAll("script");
          const promises = new Array();

          scriptNodes.forEach((node) => {
            // check if script is already loaded
            let selector: string;
            const scriptSrc: string = node.getAttribute("src");

            if (scriptSrc) {
              selector = `script[src="${scriptSrc}"]`;
            } else {
              const scriptId: string = node.getAttribute("data-falk-id");

              selector = `script[data-falk-id="${scriptId}"]`;
            }

            if (document.querySelector(selector)) {
              return;
            }

            // load script
            // We need to create a new node so our original document will run it.
            const newNode = document.createElement("script");

            for (const attribute of node.attributes) {
              newNode.setAttribute(attribute.name, attribute.value);
            }

            if (!node.src) {
              newNode.textContent = node.textContent;
            } else {
              const promise = new Promise((resolve) => {
                newNode.addEventListener("load", () => {
                  resolve(null);
                });
              });

              promises.push(promise);
            }

            document.body.appendChild(newNode);
          });

          await Promise.all(promises);

          // render HTML
          // patch entire document
          if (node.tagName == "HTML") {
            // patch the attributes of the HTML node
            // (node id, token, event handlers, ...)
            this.patchNodeAttributes(node, newDocument.children[0]);

            // patch title
            document.title = newDocument.title;

            // patch body
            this.patchNode(
              document.body,
              newDocument.body,
              eventType,
              responseData.flags,
            );

            // patch only one node in the body
          } else {
            this.patchNode(
              node,
              newDocument.body.firstChild,
              eventType,
              responseData.flags,
            );
          }

          // run hooks
          this.dispatchRenderEvents(node);

          // run callbacks
          for (const callback of responseData.callbacks) {
            this.runCallback({
              selector: callback[0],
              callbackName: callback[1],
              callbackArgs: callback[2],
            });
          }
        },
        this.parseDelay(options.delay || 0),
      );
    }
  };

  public filterEvents = (selector: string, callback: (event) => any) => {
    return (event) => {
      if (!event.target.matches(selector)) {
        return;
      }

      return callback(event);
    };
  };

  private on = (...args) => {
    const eventShortName: string = args[0];
    const eventName: string = `falk:${eventShortName}`;
    let selector: string;
    let callback: (event) => any;

    // falk.on("render", ".component#1", event => { console.log(event));
    if (args.length == 2) {
      callback = args[1];

      document.addEventListener(eventName, callback);

      // falk.on("render", event => { console.log(event));
    } else if (args.length == 3) {
      selector = args[1];
      callback = args[2];

      document.addEventListener(
        eventName,
        this.filterEvents(selector, callback),
      );
    }
  };
}

window["falk"] = new Falk();

window["falk"].init();
