export const dumpEvent = (event: Event) => {
  // TODO: add a proper `EventData` type
  const eventData = {
    eventData: {
      // contains a name like "submit" or "click"
      type: "",

      // If the target element of the event is an input, this contains
      // the value.
      data: undefined,

      // If the target element of the event is a form, this contains the
      // full form data.
      formData: {},
    },

    // multipart
    // If the target element of the event is a form that contains file
    // inputs, this contains the upload token (if present) and the file inputs
    // and all files with zero size.
    uploadToken: "",
    files: [],
  };

  const files = [];

  // The event is `undefined` when handling non-standard event handler
  // like `onRender`.
  if (!event) {
    return eventData;
  }

  eventData.eventData.type = event.type;

  // input, change, submit
  if (
    event.type == "input" ||
    event.type == "change" ||
    event.type == "submit"
  ) {
    // forms
    if (event.currentTarget instanceof HTMLFormElement) {
      const formData: FormData = new FormData(event.currentTarget);

      for (const [key, value] of formData.entries()) {
        // upload token
        if (typeof key === "string" && key == "falk/upload-token") {
          eventData.uploadToken = value as string;

          continue;
        }

        // files
        if (value instanceof File) {
          // skip empty file fields
          if (value.size > 0) {
            eventData.files.push({ key, file: value });
          }
        } else {
          // form data
          eventData.eventData.formData[key] = value;
        }
      }

      // inputs
    } else {
      const inputElement: HTMLInputElement =
        event.currentTarget as HTMLInputElement;

      eventData.eventData.data = inputElement.value;

      if (inputElement.hasAttribute("name")) {
        const inputName: string = inputElement.getAttribute("name");

        if (inputName) {
          eventData.eventData.formData[inputName] = inputElement.value;
        }
      }
    }
  }

  return eventData;
};
