"use server";

import { createProperty, updateProperty, deleteProperty } from "@/libs/api";
const propertyError = (response) => {
  if (typeof response.error === "object") {
    const errorMessages = {};

    if (response.error.title) {
      errorMessages["title"] =
        response.error.title[0][0].toUpperCase() +
        response.error.title[0].slice(1).toLowerCase();
    }

    if (response.error.description) {
      errorMessages["description"] =
        response.error.description[0][0].toUpperCase() +
        response.error.description[0].slice(1).toLowerCase();
    }

    if (response.error.price) {
      errorMessages["price"] =
        response.error.price[0][0].toUpperCase() +
        response.error.price[0].slice(1).toLowerCase();
    }

    if (response.error.beds) {
      errorMessages["property_type"] =
        response.error.property_type[0][0].toUpperCase() +
        response.error.property_type[0].slice(1).toLowerCase();
    }

    if (response.error.address) {
      errorMessages["address"] =
        response.error.address[0][0].toUpperCase() +
        response.error.address[0].slice(1).toLowerCase();
    }

    if (response.error.city) {
      //! check this
      errorMessages["beds"] =
        response.error.beds[0][0].toUpperCase() +
        response.error.beds[0].slice(1).toLowerCase();
    }

    if (response.error.state) {
      //! check this
      errorMessages["baths"] =
        response.error.baths[0][0].toUpperCase() +
        response.error.baths[0].slice(1).toLowerCase();
    }

    if (response.error.zip_code) {
      //! check this
      errorMessages["area_sqft"] =
        response.error.area_sqft[0][0].toUpperCase() +
        response.error.area_sqft[0].slice(1).toLowerCase();
    }

    if (response.error.image) {
      //! check this
      errorMessages["property_image"] = //! check this
        response.error.image_url[0][0].toUpperCase() +
        response.error.image_url[0].slice(1).toLowerCase();
    }

    return errorMessages;
  } else {
    return { general: response.error || "An unknown error occurred." };
  }
};

export const createPropertyAction = async (prevState, formData) => {
  const title = formData.get("title");
  const description = formData.get("description");
  const price = formData.get("price");
  const property_type = formData.get("property_type");
  const address = formData.get("address");
  const beds = formData.get("beds");
  const baths = formData.get("baths");
  const area_sqft = formData.get("area_sqft");
  const image_url = formData.get("image_url"); //! check this

  // ! create newPropertyData like update method

  const errors = {};

  if (!title) {
    errors.title = "Title is required.";
  }

  if (!description) {
    errors.description = "Description is required.";
  }

  if (!price) {
    errors.price = "Pricing is required.";
  }

  if (!property_type) {
    errors.property_type = "Property type is required.";
  }

  if (!address) {
    errors.address = "Please complete all required fields."; //! check this
  }

  if (!beds) {
    errors.beds = "Please complete all required fields."; //! check this
  }

  if (!baths) {
    errors.baths = "Please complete all required fields."; //! check this
  }

  if (!area_sqft) {
    errors.area_sqft = "Please complete all required fields."; //! check this
  }

  if (!image_url) {
    //! check this
    errors.image_url = "Image is required.";
  }

  if (Object.keys(errors).length > 0) {
    return {
      errors,
      success: "",
      //! create something like this formPropertyData: newPropertyFormData,
      // ! rest of them goes away
      formTitle: title || "",
      formDescription: description || "",
      formPrice: price || "",
      formPropertyType: property_type || "",
      formAddress: address || "",
      formBeds: beds || "",
      formBaths: baths || "",
      formAreaSqft: area_sqft || "",
      formImageUrl: image_url || "",
    };
  }

  try {
    //! check if the image is uploaded then send formData as it is
    //! otherwise create the json data and send it (ref userAction update method)
    const response = await createProperty(formData);

    if (response.error) {
      return {
        errors: propertyError(response),
        success: "",
        //! create something like this formPropertyData: newPropertyFormData,
        // ! rest of them goes away
        formTitle: title || "",
        formDescription: description || "",
        formPrice: price || "",
        formPropertyType: property_type || "",
        formAddress: address || "",
        formBeds: beds || "",
        formBaths: baths || "",
        formAreaSqft: area_sqft || "",
        formImageUrl: image_url || "",
      };
    }

    return {
      errors,
      success: response.success,
      //! create something like this formPropertyData: newPropertyFormData,
      formTitle: "",
      formDescription: "",
      formPrice: "",
      formPropertyType: "",
      formAddress: "",
      formBeds: "",
      formBaths: "",
      formAreaSqft: "",
      formImageUrl: "",
    };
  } catch (error) {
    console.error(error);
    errors.general = error.message || "An unexpected error occurred";
    return {
      errors,
      success: "",
      //! create something like this formPropertyData: newPropertyFormData,
      //! rest of them goes away
      formTitle: title || "",
      formDescription: description || "",
      formPrice: price || "",
      formPropertyType: property_type || "",
      formAddress: address || "",
      formBeds: beds || "",
      formBaths: baths || "",
      formAreaSqft: area_sqft || "",
      formImageUrl: image_url || "",
    };
  }
};

export const updatePropertyAction = async (id, prevState, formData) => {
  const title = formData.get("title");
  const description = formData.get("description");
  const price = formData.get("price");
  const property_type = formData.get("property_type");
  const address = formData.get("address");
  const beds = formData.get("beds");
  const baths = formData.get("baths");
  const area_sqft = formData.get("area_sqft");
  const image_url = formData.get("image_url"); //! check this

  const newPropertyData = {
    title: title || prevState.formPropertyData.title,
    description: description || prevState.formPropertyData.description,
    price: price || prevState.formPropertyData.price,
    property_type: property_type || prevState.formPropertyData.property_type,
    address: address || prevState.formPropertyData.address,
    beds: beds || prevState.formPropertyData.beds,
    baths: baths || prevState.formPropertyData.baths,
    area_sqft: area_sqft || prevState.formPropertyData.area_sqft,
    image_url: prevState.formPropertyData.image_url, //! check this
  };

  const errors = {};

  // ! full fix like create method
  if (!newPropertyData.title) {
    errors.title = "Title is required.";
  }
  if (!newPropertyData.description) {
    errors.description = "Description is required.";
  }
  if (!newPropertyData.price) {
    errors.price = "Pricing is required.";
  }
  if (!newPropertyData.property_type) {
    errors.property_type = "Property type is required.";
  }
  if (!newPropertyData.address) {
    errors.address = "Please complete all required fields.";
  }
  if (!newPropertyData.beds) {
    errors.beds = "Please complete all required fields.";
  }
  if (!newPropertyData.baths) {
    errors.baths = "Please complete all required fields.";
  }
  if (!newPropertyData.area_sqft) {
    errors.area_sqft = "Please complete all required fields.";
  }
  if (!newPropertyData.image_url) {
    errors.image_url = "Image is required.";
  }

  if (Object.keys(errors).length > 0) {
    return {
      errors,
      success: "",
      //! create something like this formPropertyData: newPropertyFormData,
      // ! rest of them goes away
      formTitle: title || "",
      formDescription: description || "",
      formPrice: price || "",
      formPropertyType: property_type || "",
      formAddress: address || "",
      formBeds: beds || "",
      formBaths: baths || "",
      formAreaSqft: area_sqft || "",
      formImageUrl: image_url || "",
    };
  }

  try {
    //! check if the image is uploaded then send formData as it is
    //! otherwise create the json data and send it (ref userAction update method)
    const response = await updateProperty(id, formData);

    if (response.error) {
      return {
        errors: propertyError(response),
        success: "",
        //! create something like this formPropertyData: newPropertyFormData,
        // ! rest of them goes away
        formTitle: title || "",
        formDescription: description || "",
        formPrice: price || "",
        formPropertyType: property_type || "",
        formAddress: address || "",
        formBeds: beds || "",
        formBaths: baths || "",
        formAreaSqft: area_sqft || "",
        formImageUrl: image_url || "",
      };
    }
    return {
      errors,
      success: response.success,
      //! create something like this formPropertyData: response.data,
      formTitle: "",
      formDescription: "",
      formPrice: "",
      formPropertyType: "",
      formAddress: "",
      formBeds: "",
      formBaths: "",
      formAreaSqft: "",
      formImageUrl: "",
    };
  } catch (error) {
    console.error(error);
    errors.general = error.message || "An unexpected error occurred";
    return {
      errors,
      success: "",
      //! create something like this formPropertyData: newPropertyFormData,
      // ! rest of them goes away
      formTitle: title || "",
      formDescription: description || "",
      formPrice: price || "",
      formPropertyType: property_type || "",
      formAddress: address || "",
      formBeds: beds || "",
      formBaths: baths || "",
      formAreaSqft: area_sqft || "",
      formImageUrl: image_url || "",
    };
  }
};

export const deletePropertyAction = async (id) => {
  try {
    const response = await deleteProperty(id);

    if (response.error) {
      return { error: response.error };
    }

    return { success: response.success };
  } catch (error) {
    console.error(error);
    return { error: error.message || "An unexpected error occurred" };
  }
};
