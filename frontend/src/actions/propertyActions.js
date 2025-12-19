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
      errorMessages["image_url"] =
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
  //! property_type doesn't exist in backend documentation
  const property_type = formData.get("property_type");
  const address = formData.get("address");
  const beds = formData.get("beds");
  const baths = formData.get("baths");
  const area_sqft = formData.get("area_sqft");
  const property_image = formData.get("property_image");
  console.log("property_image", property_image);

  const newPropertyData = {
    title: title || prevState.formPropertyData.title,
    description: description || prevState.formPropertyData.description,
    price: price || prevState.formPropertyData.price,
    //! property_type doesn't exist in backend documentation
    property_type: property_type || prevState.formPropertyData.property_type,
    address: address || prevState.formPropertyData.address,
    beds: beds || prevState.formPropertyData.beds,
    baths: baths || prevState.formPropertyData.baths,
    area_sqft: area_sqft || prevState.formPropertyData.area_sqft,
    property_image: property_image || prevState.formPropertyData.property_image,
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

  //! property_type doesn't exist in backend documentation
  if (!property_type) {
    errors.property_type = "Property type is required.";
  }

  //! instead of this handle each address property
  //! format them to address to string then
  //! "flatNo=2, houseNo=2, street=2, area=2, city=2, state=2, country=2";
  if (!address) {
    errors.address = "Address is required.";
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
      //! remove the $ sign fields before pushing
      // const keys_to_delete = [];
      // for (const [key, _] of formData.entries()) {
      //   if (
      //     key.startsWith("$") ||
      //     key === ""
      //   ) {
      //     keys_to_delete.push(key);
      //   }
      // }

      // for (const key of keys_to_delete) {
      //   formData.delete(key);
      // }

      response = await createProperty(formData, true);
    } else {
      const data = {
        title,
        description,
        price,
        property_type,
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

//! property_type doesn't exist in backend documentation
export const updatePropertyAction = async (id, prevState, formData) => {
  const title = formData.get("title");
  const description = formData.get("description");
  const price = formData.get("price");
  const property_type = formData.get("property_type");
  const address = formData.get("address");
  const beds = formData.get("beds");
  const baths = formData.get("baths");
  const area_sqft = formData.get("area_sqft");
  const property_image = formData.get("property_image");

  const newPropertyData = {
    title: title || prevState.formPropertyData.title,
    description: description || prevState.formPropertyData.description,
    price: price || prevState.formPropertyData.price,
    property_type: property_type || prevState.formPropertyData.property_type,
    address: address || prevState.formPropertyData.address,
    beds: beds || prevState.formPropertyData.beds,
    baths: baths || prevState.formPropertyData.baths,
    area_sqft: area_sqft || prevState.formPropertyData.area_sqft,
    property_image: prevState.formPropertyData.property_image,
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
  if (!newPropertyData.property_type) {
    errors.property_type = "Property type is required.";
  }
  //! instead of this handle each address property
  //! format them to address to string then
  //! "flatNo=2, houseNo=2, street=2, area=2, city=2, state=2, country=2";
  if (!newPropertyData.address) {
    errors.address = "Address is required.";
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

    //! remove the $ sign fields before pushing
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
        ...(property_type &&
          property_type !== prevState.formPropertyData.property_type && {
            property_type,
          }),
        ...(address &&
          address !== prevState.formPropertyData.address && { address }),
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
