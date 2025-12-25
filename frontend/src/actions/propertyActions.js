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

    if (response.error.address) {
      errorMessages["address"] =
        response.error.address[0][0].toUpperCase() +
        response.error.address[0].slice(1).toLowerCase();
    }

    if (response.error.beds) {
      errorMessages["beds"] =
        response.error.beds[0][0].toUpperCase() +
        response.error.beds[0].slice(1).toLowerCase();
    }

    if (response.error.baths) {
      errorMessages["baths"] =
        response.error.baths[0][0].toUpperCase() +
        response.error.baths[0].slice(1).toLowerCase();
    }

    if (response.error.area_sqft) {
      errorMessages["area_sqft"] =
        response.error.area_sqft[0][0].toUpperCase() +
        response.error.area_sqft[0].slice(1).toLowerCase();
    }

    if (response.error.image_url) {
      if (Array.isArray(response.error.image_url)) {
        errorMessages["image_url"] = response.error.image_url;
      } else if (typeof response.error.image_url === "object") {
        const image_error = response.error.image_url;
        let image_errors = [];

        if (image_error.size) {
          image_errors.push(image_error.size);
        }

        if (image_error.type) {
          image_errors.push(image_error.type);
        }

        errorMessages["image_url"] = image_errors.join(" ");
      } else {
        errorMessages["image_url"] =
          response.error.image_url[0][0].toUpperCase() +
          response.error.image_url[0].slice(1).toLowerCase();
      }
    }

    return errorMessages;
  } else {
    return { general: response.error || "An unknown error occurred." };
  }
};

export const createPropertyAction = async (prevState, formData) => {
  const addressParts = {
    flatNo: formData.get("flatNo") || "",
    houseNo: formData.get("houseNo") || "",
    street: formData.get("street") || "",
    area: formData.get("area") || "",
    city: formData.get("city") || "",
    state: formData.get("state") || "",
    country: formData.get("country") || "",
  };

  const title = formData.get("title");
  const description = formData.get("description");
  const price = formData.get("price");

  const address = Object.entries(addressParts)
    .map(([key, value]) => `${key}=${value}`)
    .join(", ");

  formData.set("address", address);

  const beds = formData.get("beds");
  const baths = formData.get("baths");
  const area_sqft = formData.get("area_sqft");
  const property_image = formData.get("property_image");

  const newPropertyData = {
    title: title || prevState.formPropertyData.title,
    description: description || prevState.formPropertyData.description,
    price: price || prevState.formPropertyData.price,
    beds: beds || prevState.formPropertyData.beds,
    baths: baths || prevState.formPropertyData.baths,
    area_sqft: area_sqft || prevState.formPropertyData.area_sqft,
    property_image: property_image || prevState.formPropertyData.property_image,
    ...addressParts,
  };

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

  const requiredAddressFields = [
    "houseNo",
    "street",
    "area",
    "city",
    "state",
    "country",
  ];
  const missing = requiredAddressFields.filter(
    (field) => !addressParts[field].trim(),
  );

  if (missing.length > 0) {
    errors.address =
      "Please provide full address: House No, Street, Area, City, State, and Country are required.";
  }

  if (!beds) {
    errors.beds = "Number of Beds is required.";
  }

  if (!baths) {
    errors.baths = "Number of Baths is required.";
  }

  if (!area_sqft) {
    errors.area_sqft = "Area is required.";
  }

  if (!property_image) {
    errors.image_url = "Image is required.";
  }

  if (Object.keys(errors).length > 0) {
    return {
      errors,
      success: "",
      formPropertyData: newPropertyData,
    };
  }

  try {
    let response;
    const isNewImageUploaded =
      property_image &&
      property_image instanceof File &&
      property_image.size > 0;

    if (isNewImageUploaded) {
      response = await createProperty(formData, true);
    } else {
      const data = {
        title,
        description,
        price,
        address,
        beds,
        baths,
        area_sqft,
      };
      response = await createProperty(data);
    }

    if (response.error) {
      return {
        errors: propertyError(response),
        success: "",
        formPropertyData: newPropertyData,
      };
    }

    return {
      errors,
      success: response.success,
      formPropertyData: newPropertyData,
    };
  } catch (error) {
    console.error(error);
    errors.general = error.message || "An unexpected error occurred";
    return {
      errors,
      success: "",
      formPropertyData: newPropertyData,
    };
  }
};

export const updatePropertyAction = async (id, prevState, formData) => {
  const addressParts = {
    flatNo: formData.get("flatNo") || "",
    houseNo: formData.get("houseNo") || "",
    street: formData.get("street") || "",
    area: formData.get("area") || "",
    city: formData.get("city") || "",
    state: formData.get("state") || "",
    country: formData.get("country") || "",
  };

  const addressString = Object.entries(addressParts)
    .map(([key, value]) => `${key}=${value}`)
    .join(", ");

  const title = formData.get("title");
  const description = formData.get("description");
  const price = formData.get("price");
  formData.set("address", addressString);
  const beds = formData.get("beds");
  const baths = formData.get("baths");
  const area_sqft = formData.get("area_sqft");
  const property_image = formData.get("property_image");

  const newPropertyData = {
    title: title || prevState.formPropertyData.title,
    description: description || prevState.formPropertyData.description,
    price: price || prevState.formPropertyData.price,
    beds: beds || prevState.formPropertyData.beds,
    baths: baths || prevState.formPropertyData.baths,
    area_sqft: area_sqft || prevState.formPropertyData.area_sqft,
    property_image: prevState.formPropertyData.property_image,
    ...addressParts,
  };

  const errors = {};

  if (!newPropertyData.title) {
    errors.title = "Title is required.";
  }
  if (!newPropertyData.description) {
    errors.description = "Description is required.";
  }
  if (!newPropertyData.price) {
    errors.price = "Pricing is required.";
  }

  const requiredAddressFields = [
    "houseNo",
    "street",
    "area",
    "city",
    "state",
    "country",
  ];
  const missing = requiredAddressFields.filter(
    (field) => !addressParts[field].trim(),
  );

  if (missing.length > 0) {
    errors.address =
      "Please provide full address: House No, Street, Area, City, State, and Country are required.";
  }
  if (!newPropertyData.beds) {
    errors.beds = "Number of Beds is required.";
  }
  if (!newPropertyData.baths) {
    errors.baths = "Number of Baths is required.";
  }
  if (!newPropertyData.area_sqft) {
    errors.area_sqft = "Area is required.";
  }
  if (!newPropertyData.property_image) {
    errors.image_url = "Image is required.";
  }

  if (Object.keys(errors).length > 0) {
    return {
      errors,
      success: "",
      formPropertyData: newPropertyData,
    };
  }

  try {
    let response;
    const isNewImageUploaded =
      property_image &&
      property_image instanceof File &&
      property_image.size > 0;

    if (isNewImageUploaded) {
      response = await updateProperty(id, formData, true);
    } else {
      const data = {
        ...(title && title !== prevState.formPropertyData.title && { title }),
        ...(description &&
          description !== prevState.formPropertyData.description && {
            description,
          }),
        ...(price && price !== prevState.formPropertyData.price && { price }),
        ...(addressString &&
          addressString !== prevState.formPropertyData.address && {
            address: addressString,
          }),
        ...(beds && beds !== prevState.formPropertyData.beds && { beds }),
        ...(baths && baths !== prevState.formPropertyData.baths && { baths }),
        ...(area_sqft &&
          area_sqft !== prevState.formPropertyData.area_sqft && { area_sqft }),
      };

      response = await updateProperty(id, data);
    }

    if (response.error) {
      return {
        errors: propertyError(response),
        success: "",
        formPropertyData: newPropertyData,
      };
    }
    return {
      errors,
      success: response.success,
      formPropertyData: response.data,
    };
  } catch (error) {
    console.error(error);
    errors.general = error.message || "An unexpected error occurred";
    return {
      errors,
      success: "",
      formPropertyData: newPropertyData,
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
