"use client";

import { useState, useEffect, useActionState, useRef } from "react";
import { useRouter } from "next/navigation";
import Form from "next/form";
import Image from "next/image";
import Link from "next/link";
import { createPropertyAction } from "@/actions/propertyActions";
import { FormButton } from "@/components/buttons/Buttons";
import styles from "./CreateListingForm.module.css";

const initialState = {
  errors: {},
  success: "",
  formPropertyData: {
    title: "",
    description: "",
    country: "",
    state: "",
    city: "",
    area: "",
    street: "",
    houser_no: "",
    flat_no: "",
    beds: "",
    baths: "",
    area_sqft: "",
    price: "",
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
  const router = useRouter();
  const [previewUrl, setPreviewUrl] = useState(null);
  const fileInputRef = useRef(null);
  const [localImageError, setLocalImageError] = useState("");
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    country: "",
    state: "",
    city: "",
    area: "",
    street: "",
    houser_no: "",
    flat_no: "",
    beds: "",
    baths: "",
    area_sqft: "",
    price: "",
    property_image: null,
  });

  const resetImageInput = () => {
    setPreviewUrl(state.formPropertyData.image_url);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setLocalImageError("");
      const validTypes = ["image/jpeg", "image/png", "image/jpg"];
      const isInvalidType = !validTypes.includes(file.type);
      const isTooLarge = file.size > 2 * 1024 * 1024;

      if (isInvalidType || isTooLarge) {
        const msg = isInvalidType
          ? "Only JPG, JPEG and PNG images are allowed."
          : "Image size should not exceed 2MB.";

        setLocalImageError(msg);
        resetImageInput();
        return;
      }

      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }

      setPreviewUrl(URL.createObjectURL(file));
      setFormData((prev) => ({ ...prev, property_image: file }));
    }
  };

  const handleRemoveImage = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setFormData((prev) => ({ ...prev, property_image: null }));

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleIconClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  useEffect(() => {
    if (state.errors && state.errors.image_url) {
      resetImageInput();
    }
  }, [state.errors]);

  useEffect(() => {
    if (state.success) {
      setTimeout(() => {
        router.push("/");
      }, 2000);
      setLocalImageError("");
    }
  }, [state.success, router]);

  const isTitleComplete = formData.title.trim() !== "";
  const isDescriptionComplete = formData.description.trim() !== "";
  const isAddressComplete =
    formData.country.trim() !== "" &&
    formData.state.trim() !== "" &&
    formData.city.trim() !== "" &&
    formData.area.trim() !== "" &&
    formData.street.trim() !== "" &&
    formData.houser_no.trim() !== "";
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
          <div className={styles.sidebarResponsiveWrapper}>
            <div className={styles.sidebarHeader}>
              <div className={styles.sidebarTitle}>Create a listing</div>
              <div className={styles.sidebarSubtitle}>
                Input property information
              </div>
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
      </div>

      <div className={styles.formContainer}>
        <Form action={formAction}>
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
            {Object.keys(state.errors).length > 0 && state.errors.title && (
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
            {Object.keys(state.errors).length > 0 &&
              state.errors.description && (
                <div className={styles.errorBox}>
                  {state.errors.description}
                </div>
              )}
          </div>
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
                  name="houser_no"
                  value={formData.houser_no}
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
                name="flat_no"
                value={formData.flat_no}
                onChange={handleInputChange}
                className={styles.input}
              />
            </div>
            {Object.keys(state.errors).length > 0 && state.errors.address && (
              <div className={styles.errorBox}>{state.errors.address}</div>
            )}
          </div>
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
                {Object.keys(state.errors).length > 0 && state.errors.beds && (
                  <div className={styles.errorBox}>{state.errors.beds}</div>
                )}
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
                {Object.keys(state.errors).length > 0 && state.errors.baths && (
                  <div className={styles.errorBox}>{state.errors.baths}</div>
                )}
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
                {Object.keys(state.errors).length > 0 &&
                  state.errors.area_sqft && (
                    <div className={styles.errorBox}>
                      {state.errors.area_sqft}
                    </div>
                  )}
              </div>
            </div>
          </div>
          <div className={styles.section}>
            <div className={styles.sectionTitle}>Pricing</div>
            <div className={styles.priceInputWrapper}>
              <div className={styles.dollarSign}>$</div>
              <input
                type="number"
                name="price"
                placeholder="0.00"
                value={formData.price}
                onChange={handleInputChange}
                className={styles.priceInput}
              />
            </div>
            {Object.keys(state.errors).length > 0 && state.errors.price && (
              <div className={styles.errorBox}>{state.errors.price}</div>
            )}
          </div>
          <div className={styles.section}>
            <div className={styles.sectionTitle}>Image</div>
            <div className={styles.imageUploadBox}>
              <div className={styles.imagePreviewContainer}>
                {previewUrl ? (
                  <>
                    <Image
                      src={previewUrl}
                      alt="Preview"
                      width={400}
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
                  </>
                ) : (
                  <div className={styles.imagePlaceholder}>
                    <Image
                      src="/assets/placeholder.png"
                      alt="Placeholder"
                      width={400}
                      height={300}
                      className={styles.imagePlaceholder}
                    />
                  </div>
                )}
              </div>

              <div className={styles.uploadControlSide}>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleImageChange}
                  name="property_image"
                  accept="image/*"
                  className={styles.imageInput}
                  disabled={isPending}
                />
                <div className={styles.uploadLabel}>
                  <div
                    className={styles.uploadIconCircle}
                    onClick={handleIconClick}
                  >
                    <Image
                      src={uploadIcon}
                      alt="Upload"
                      width={30}
                      height={30}
                    />
                  </div>
                  <div className={styles.uploadText}>Choose File to Upload</div>
                  <div className={styles.uploadSubtext}>
                    Maximum Upload Size 2MB
                  </div>
                </div>
              </div>
            </div>
            {localImageError ? (
              <span className={styles.errorBox}>{localImageError}</span>
            ) : Object.keys(state.errors).length > 0 &&
              state.errors.image_url ? (
              <span className={styles.errorText}>{state.errors.image_url}</span>
            ) : null}
          </div>
          {state.success && (
            <div className={styles.successBox}>{state.success}</div>
          )}
          {Object.keys(state.errors).length > 0 && state.errors.general && (
            <div className={styles.errorBox}>{state.errors.general}</div>
          )}
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
