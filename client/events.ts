import { EventData } from "./types";

export const dumpEvent = (event: Event | undefined) => {
  const eventData: EventData = {
    eventData: {
      type: "",
      data: undefined,
      form_data: {},
    },
    uploadToken: "",
    files: [],
  };

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
            eventData.files.push({ key: key, file: value });
          }
        } else {
          // form data
          eventData.eventData.form_data[key] = value;
        }
      }

      // inputs
    } else {
      const inputElement: HTMLInputElement =
        event.currentTarget as HTMLInputElement;

      eventData.eventData.data = inputElement.value;

      if (inputElement.hasAttribute("name")) {
        const inputName: string = inputElement.getAttribute("name") as string;

        if (inputName) {
          eventData.eventData.form_data[inputName] = inputElement.value;
        }
      }
    }
  }

  return eventData;
};
