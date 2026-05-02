export type MutationRequestResponse = {
  valid: boolean;

  httpResponse?: any;

  flags?: Record<string, boolean>;
  body?: string;
  tokens?: Record<string, string>;
  callbacks?: Array<Array<any>>;
};

export type EventData = {
  // keys in `eventData` contain underscores so they are consistent with
  // other data structures on the server
  eventData: {
    // contains a name like "submit" or "click"
    type: string;

    // If the target element of the event is an input, this contains
    // the value.
    data: string | undefined;

    // If the target element of the event is a form, this contains the
    // full form data.
    form_data: Record<string, FormDataEntryValue>;
  };

  // multipart
  // If the target element of the event is a form that contains file
  // inputs, this contains the upload token (if present) and the file inputs
  // and all files with zero size.
  uploadToken: string;
  files: Array<{ key: string; file: File }>;
};
