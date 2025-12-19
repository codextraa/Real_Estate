"use client";

import { useState, useEffect, useActionState, useRef } from "react";
import Form from "next/form";
import Image from "next/image";
import Link from "next/link";
import { createPropertyAction } from "@/actions/propertyActions";
import { FormButton } from "@/components/buttons/Buttons";
import styles from "./ListingForm.module.css";

const initialState = {
  errors: {},
  success: "",
  formPropertyData: {
    title: "",
    description: "",
    price: "",
    //! property_type doesn't exist in backend documentation
    property_type: "house",
    address: "",
    beds: "",
    baths: "",
    area_sqft: "",
    property_image: null,
  },
};
const uploadIcon = "/assets/upload-icon.svg";
const doneIcon = "/assets/done.svg";
const notDoneIcon = "/assets/not-done.svg";

export default function ListingForm() {
  const [state, formAction, isPending] = useActionState(
    createPropertyAction,
    initialState,
  );
  const [previewUrl, setPreviewUrl] = useState(null);
  const fileInputRef = useRef(null);
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    country: "",
    state: "",
    city: "",
    area: "",
    street: "",
    houseNo: "",
    flatNo: "",
    beds: "",
    baths: "",
    area_sqft: "",
    price: "",
    property_image: null,
  });

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (previewUrl) {
        //! revoke this why?? what is this??
        URL.revokeObjectURL(previewUrl);
      }
      setPreviewUrl(URL.createObjectURL(file));
      setFormData((prev) => ({ ...prev, property_image: file }));
    }
  };

  const handleIconClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleRemoveImage = () => {
    if (previewUrl) {
      //! revoke this why?? what is this??
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setFormData((prev) => ({ ...prev, property_image: null }));

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  useEffect(() => {
    return () => {
      //! revoke this why?? what is this??
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  //! success state handling

  //! address problem needs to be addressed
  //! "flatNo=2, houseNo=2, street=2, area=2, city=2, state=2, country=2";
  const formattedAddress = [
    formData.flatNo,
    formData.houseNo,
    formData.street,
    formData.area,
    formData.city,
    formData.state,
    formData.country,
  ]
    .filter((val) => val && val.trim() !== "")
    .join(", ");

  const isTitleComplete = formData.title.trim() !== "";
  const isDescriptionComplete = formData.description.trim() !== "";
  const isAddressComplete =
    formData.country.trim() !== "" &&
    formData.state.trim() !== "" &&
    formData.city.trim() !== "" &&
    formData.area.trim() !== "" &&
    formData.street.trim() !== "" &&
    formData.houseNo.trim() !== "";
  const isDetailsComplete =
    formData.beds.trim() !== "" &&
    formData.baths.trim() !== "" &&
    formData.area_sqft.trim() !== "";
  const isPricingComplete = formData.price.trim() !== "";
  const isImageComplete = formData.property_image !== null;

  return (
    <div className={styles.container}>
      <div className={styles.sidebar}>
        <div className={styles.sidebarContent}>
          <div className={styles.sidebarTitle}>Create a listing</div>
          <div className={styles.sidebarSubtitle}>
            Input property information
          </div>
          <div className={styles.checklist}>
            {[
              { label: "Title", check: isTitleComplete },
              { label: "Description", check: isDescriptionComplete },
              { label: "Address", check: isAddressComplete },
              { label: "Details", check: isDetailsComplete },
              { label: "Pricing", check: isPricingComplete },
              { label: "Image", check: isImageComplete },
            ].map((item, idx) => (
              <div key={idx} className={styles.checkItem}>
                <div className={styles.iconContainer}>
                  <Image
                    src={item.check ? doneIcon : notDoneIcon}
                    alt="status"
                    width={24}
                    height={24}
                  />
                </div>
                <div className={styles.label}>{item.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className={styles.formContainer}>
        <Form action={formAction}>
          <input type="hidden" name="address" value={formattedAddress} />
          //! property type doesn't exist in backend
          <input type="hidden" name="property_type" value="house" />
          <div className={styles.section}>
            <div className={styles.sectionTitle}>Title</div>
            <input
              type="text"
              name="title"
              value={formData.title}
              placeholder="Title"
              onChange={handleInputChange}
              className={styles.input}
            />
            {state.errors?.title && (
              <div className={styles.errorBox}>{state.errors.title}</div>
            )}
          </div>
          <div className={styles.section}>
            <div className={styles.sectionTitle}>Description</div>
            <textarea
              name="description"
              placeholder="Description"
              value={formData.description}
              onChange={handleInputChange}
              className={styles.input}
              maxLength={150}
            />
            //! object error length add in all errors
            {state.errors?.description && (
              <div className={styles.errorBox}>{state.errors.description}</div>
            )}
          </div>
          //! no grid three div here it needs to be handled differently //! no
          name for these fields so that they don't go to actions
          <div className={styles.section}>
            <div className={styles.sectionTitle}>Address</div>
            <div className={styles.gridThree}>
              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Country*</h1>
                <input
                  type="text"
                  placeholder="Country"
                  name="country"
                  value={formData.country}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>State*</h1>
                <input
                  type="text"
                  placeholder="State"
                  name="state"
                  value={formData.state}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>
              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>City*</h1>
                <input
                  type="text"
                  placeholder="City"
                  name="city"
                  value={formData.city}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>
            </div>
            <div className={styles.gridThree}>
              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Area*</h1>
                <input
                  type="text"
                  placeholder="Area"
                  name="area"
                  value={formData.area}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>
              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Street*</h1>
                <input
                  type="text"
                  placeholder="Street"
                  name="street"
                  value={formData.street}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>
              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>House No.*</h1>
                <input
                  type="text"
                  placeholder="House No."
                  name="houseNo"
                  value={formData.houseNo}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>
            </div>
            <div className={styles.inputContainer}>
              <h1 className={styles.inputTitle}>Flat No. (optional)</h1>
              <input
                type="text"
                placeholder="Flat No."
                name="flatNo"
                value={formData.flatNo}
                onChange={handleInputChange}
                className={styles.input}
              />
            </div>
            {state.errors?.address && (
              <div className={styles.errorBox}>{state.errors.address}</div>
            )}
          </div>
          //! no grid three div here it needs to be handled differently
          <div className={styles.section}>
            <div className={styles.sectionTitle}>Details</div>
            <div className={styles.gridThree}>
              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Beds*</h1>
                <input
                  type="number"
                  placeholder="Beds"
                  name="beds"
                  value={formData.beds}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>
              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Baths*</h1>
                <input
                  type="number"
                  placeholder="Baths"
                  name="baths"
                  value={formData.baths}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>
              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Sqft*</h1>
                <input
                  type="number"
                  placeholder="Sqft"
                  name="area_sqft"
                  value={formData.area_sqft}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>
            </div>
            //! each error will be inside of the divs
            {state.errors?.beds && (
              <div className={styles.errorBox}>{state.errors.beds}</div>
            )}
            {state.errors?.baths && (
              <div className={styles.errorBox}>{state.errors.baths}</div>
            )}
            {state.errors?.area_sqft && (
              <div className={styles.errorBox}>{state.errors.area_sqft}</div>
            )}
          </div>
          //! problem in styles $ not coming before text
          <div className={styles.section}>
            <div className={styles.sectionTitle}>Pricing</div>
            <div className={styles.priceInputWrapper}>
              <div className={styles.dollarSign}>$</div>
              <input
                type="number"
                name="price"
                value={formData.price}
                onChange={handleInputChange}
                className={styles.input}
              />
            </div>
            {state.errors?.price && (
              <div className={styles.errorBox}>{state.errors.price}</div>
            )}
          </div>
          //! not conditional this will split the box in two like design
          <div className={styles.section}>
            <div className={styles.sectionTitle}>Image</div>
            <div className={styles.imageUploadBox}>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageChange}
                name="property_image"
                accept="image/*"
                className={styles.imageInput}
                disabled={isPending}
              />
              {!previewUrl ? (
                <div className={styles.uploadLabel}>
                  <Image
                    src={uploadIcon}
                    onClick={handleIconClick}
                    alt="Upload"
                    width={50}
                    height={50}
                  />
                  <div className={styles.uploadText}>Choose File to Upload</div>
                  <div className={styles.uploadText}>
                    Maximum Upload Size 2MB{" "}
                  </div>
                </div>
              ) : (
                <div className={styles.imagePreviewContainer}>
                  <Image
                    src={previewUrl}
                    alt="Preview"
                    width={300}
                    height={300}
                    className={styles.imagePreview}
                  />
                  <button
                    type="button"
                    className={styles.deleteImageBtn}
                    onClick={handleRemoveImage}
                  >
                    X
                  </button>
                </div>
              )}
            </div>
            {state.errors?.image_url && (
              <div className={styles.errorBox}>{state.errors.image_url}</div>
            )}
          </div>
          {state.success && (
            <div className={styles.successBox}>{state.success}</div>
          )}
          //! where is the general error??
          <div className={styles.buttonGroup}>
            <div className={styles.cancelProfileButton}>
              <Link href={`/`}>Cancel</Link>
            </div>
            <FormButton
              type="submit"
              text="Create"
              pendingText="Creating..."
              disabled={isPending}
              className={styles.submitBtn}
            />
          </div>
        </Form>
      </div>
    </div>
  );
}
